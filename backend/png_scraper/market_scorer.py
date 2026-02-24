"""
PNG Real Estate — Market Value Scoring Engine
==============================================
Compares a Facebook listing's price against the average of formal-site
(Hausples) listings in the same suburb and returns a 'Market Value' score:
    'Deal'       — ≥15% below suburb average
    'Fair'       — within ±15% of suburb average
    'Overpriced' — ≥15% above suburb average

Also handles: insufficient data, cross-suburb fallback, confidence ratings.
"""

import json
import math
from dataclasses import dataclass, asdict, field
from typing import Optional
from enum import Enum


# ── ENUMS & MODELS ────────────────────────────────────────────────────────────

class MarketLabel(str, Enum):
    DEAL        = "Deal"
    FAIR        = "Fair"
    OVERPRICED  = "Overpriced"
    UNKNOWN     = "Unknown"         # insufficient data


class DataConfidence(str, Enum):
    HIGH   = "High"     # ≥5 formal listings in suburb
    MEDIUM = "Medium"   # 2–4 formal listings
    LOW    = "Low"      # 1 listing or city-wide fallback


@dataclass
class SuburbStats:
    suburb: str
    sample_size: int
    avg_price: float
    median_price: float
    std_dev: float
    min_price: float
    max_price: float
    confidence: DataConfidence


@dataclass
class MarketValueResult:
    # Input
    fb_price: int
    suburb: str
    property_type: Optional[str]

    # Benchmark
    benchmark_avg: Optional[float]
    benchmark_median: Optional[float]
    benchmark_sample_size: int
    benchmark_confidence: DataConfidence

    # Score
    label: MarketLabel
    pct_vs_avg: Optional[float]       # e.g. +22.5 means 22.5% above avg
    pct_vs_median: Optional[float]

    # Human readable
    summary: str
    recommendation: str

    # Thresholds used
    deal_threshold_pct: float = 15.0
    overpriced_threshold_pct: float = 15.0


# ── FORMAL LISTING DATABASE (replace with live MongoDB query in production) ───

# Format: suburb (lowercase) → list of monthly PGK prices from Hausples
FORMAL_LISTINGS_DB: dict[str, list[int]] = {
    "waigani": [4500, 4200, 5000, 3900, 4800, 4100, 5500, 3800, 4300, 4600],
    "boroko":  [3200, 2800, 3500, 3100, 2900, 3400, 3000, 3300, 2700, 3600],
    "gerehu":  [1800, 2100, 1600, 1900, 2000, 1750, 1850, 2200, 1650, 1950],
    "gordons": [5800, 6200, 5500, 6500, 5900, 6100, 5700],
    "hohola":  [1500, 1700, 1600, 1400, 1800],
    "tokarara":[2200, 2400, 2100, 2300, 2500, 2150],
    "koki":    [2900, 3100, 2800, 3000, 2700],
    "badili":  [3400, 3200, 3600, 3100],
    "six mile":[1400, 1600, 1500, 1300, 1450],
    "eight mile": [1200, 1350, 1250, 1100],
    "morata":  [1600, 1800, 1500],
    "erima":   [2000, 2200, 1900],
}

# City-wide fallback (all suburbs combined)
ALL_CITY_PRICES = [p for prices in FORMAL_LISTINGS_DB.values() for p in prices]


# ── STATS HELPERS ─────────────────────────────────────────────────────────────

def compute_stats(prices: list[int], suburb: str) -> SuburbStats:
    n = len(prices)
    if n == 0:
        return SuburbStats(suburb, 0, 0, 0, 0, 0, 0, DataConfidence.LOW)

    avg = sum(prices) / n
    sorted_p = sorted(prices)
    mid = n // 2
    median = sorted_p[mid] if n % 2 else (sorted_p[mid - 1] + sorted_p[mid]) / 2
    variance = sum((p - avg) ** 2 for p in prices) / n
    std_dev = math.sqrt(variance)

    if n >= 5:
        conf = DataConfidence.HIGH
    elif n >= 2:
        conf = DataConfidence.MEDIUM
    else:
        conf = DataConfidence.LOW

    return SuburbStats(
        suburb=suburb,
        sample_size=n,
        avg_price=round(avg, 2),
        median_price=round(median, 2),
        std_dev=round(std_dev, 2),
        min_price=min(prices),
        max_price=max(prices),
        confidence=conf,
    )


def get_suburb_stats(suburb: str) -> Optional[SuburbStats]:
    """
    Get stats for the given suburb. Falls back to city-wide if no data.
    Returns None only if absolutely no data exists anywhere.
    """
    key = suburb.strip().lower()
    prices = FORMAL_LISTINGS_DB.get(key)

    if prices and len(prices) >= 1:
        return compute_stats(prices, suburb)

    # Try partial match (e.g. "Gerehu Stage 3" → "gerehu")
    for db_key, db_prices in FORMAL_LISTINGS_DB.items():
        if db_key in key or key in db_key:
            return compute_stats(db_prices, suburb)

    # City-wide fallback
    if ALL_CITY_PRICES:
        stats = compute_stats(ALL_CITY_PRICES, "Port Moresby (city-wide)")
        stats.confidence = DataConfidence.LOW
        return stats

    return None


# ── PROPERTY TYPE ADJUSTMENT ──────────────────────────────────────────────────

# Multipliers relative to "House" baseline (derived from PNG market observation)
PROPERTY_TYPE_ADJUSTMENTS = {
    "house":      1.00,
    "apartment":  0.90,
    "studio":     0.65,
    "room":       0.35,
    "townhouse":  0.95,
    "compound":   1.15,
    "commercial": 1.40,
    "land":       0.50,
}

def get_type_adjusted_avg(raw_avg: float, property_type: Optional[str]) -> float:
    """
    Adjust the suburb average for property type differences.
    E.g. if the suburb avg includes houses but the listing is a Studio,
    we expect it to be ~65% of the house price.
    """
    if not property_type:
        return raw_avg
    multiplier = PROPERTY_TYPE_ADJUSTMENTS.get(property_type.lower(), 1.0)
    return raw_avg * multiplier


# ── SCORING THRESHOLDS ────────────────────────────────────────────────────────

DEAL_THRESHOLD        = 15.0    # % below avg → "Deal"
OVERPRICED_THRESHOLD  = 15.0    # % above avg → "Overpriced"
STRONG_DEAL           = 30.0    # % below → "Strong Deal"
STRONG_OVERPRICED     = 30.0    # % above → "Severely Overpriced"


# ── MAIN SCORING FUNCTION ─────────────────────────────────────────────────────

def score_market_value(
    fb_price_monthly_pgk: int,
    suburb: str,
    property_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    deal_threshold: float = DEAL_THRESHOLD,
    overpriced_threshold: float = OVERPRICED_THRESHOLD,
) -> MarketValueResult:
    """
    Compare a Facebook listing price against formal-site averages.

    Args:
        fb_price_monthly_pgk: Normalized monthly price in PGK (from normalizer.py)
        suburb:               Suburb name (e.g. "Boroko")
        property_type:        Optional — "House", "Apartment", "Room", etc.
        bedrooms:             Optional — used for future bedroom-cohort analysis
        deal_threshold:       % below avg to be called a Deal (default 15)
        overpriced_threshold: % above avg to be called Overpriced (default 15)

    Returns:
        MarketValueResult dataclass with all scoring details
    """

    stats = get_suburb_stats(suburb)

    # ── No data at all ─────────────────────────────────────────────────────
    if stats is None or stats.avg_price == 0:
        return MarketValueResult(
            fb_price=fb_price_monthly_pgk,
            suburb=suburb,
            property_type=property_type,
            benchmark_avg=None,
            benchmark_median=None,
            benchmark_sample_size=0,
            benchmark_confidence=DataConfidence.LOW,
            label=MarketLabel.UNKNOWN,
            pct_vs_avg=None,
            pct_vs_median=None,
            summary=f"No formal listing data available for {suburb}.",
            recommendation="Cannot assess — check Hausples manually for this area.",
        )

    # ── Adjust benchmark for property type ─────────────────────────────────
    adjusted_avg    = get_type_adjusted_avg(stats.avg_price, property_type)
    adjusted_median = get_type_adjusted_avg(stats.median_price, property_type)

    # ── Compute deviation ──────────────────────────────────────────────────
    pct_vs_avg    = ((fb_price_monthly_pgk - adjusted_avg) / adjusted_avg) * 100
    pct_vs_median = ((fb_price_monthly_pgk - adjusted_median) / adjusted_median) * 100

    # ── Assign label ───────────────────────────────────────────────────────
    if pct_vs_avg <= -deal_threshold:
        if pct_vs_avg <= -STRONG_DEAL:
            label = MarketLabel.DEAL
            quality = "strong "
        else:
            label = MarketLabel.DEAL
            quality = ""
        direction = "below"
        abs_pct = abs(pct_vs_avg)
        summary = (
            f"🟢 {quality.upper()}DEAL — K{fb_price_monthly_pgk:,}/mo is "
            f"{abs_pct:.1f}% below the {stats.suburb} average "
            f"(K{adjusted_avg:,.0f}/mo, n={stats.sample_size})."
        )
        recommendation = (
            "This listing appears underpriced vs. formal listings. "
            "Verify condition, confirm with landlord directly, and check for hidden costs."
            + (" Low data confidence — treat with caution." if stats.confidence == DataConfidence.LOW else "")
        )

    elif pct_vs_avg >= overpriced_threshold:
        if pct_vs_avg >= STRONG_OVERPRICED:
            label = MarketLabel.OVERPRICED
            quality = "severely "
        else:
            label = MarketLabel.OVERPRICED
            quality = ""
        abs_pct = abs(pct_vs_avg)
        summary = (
            f"🔴 {quality.upper()}OVERPRICED — K{fb_price_monthly_pgk:,}/mo is "
            f"{abs_pct:.1f}% above the {stats.suburb} average "
            f"(K{adjusted_avg:,.0f}/mo, n={stats.sample_size})."
        )
        recommendation = (
            "Price is above market rate. Negotiate down or consider alternatives in "
            f"{suburb}. Check if listing is from a middleman/agent adding markup."
        )

    else:
        label = MarketLabel.FAIR
        direction = "above" if pct_vs_avg > 0 else "below"
        abs_pct = abs(pct_vs_avg)
        summary = (
            f"🟡 FAIR — K{fb_price_monthly_pgk:,}/mo is {abs_pct:.1f}% {direction} "
            f"the {stats.suburb} average (K{adjusted_avg:,.0f}/mo, n={stats.sample_size})."
        )
        recommendation = (
            "Price is within normal market range. Still worth negotiating 5–10% lower "
            "as informal listings often have flexibility."
        )

    # ── Confidence caveat ──────────────────────────────────────────────────
    if stats.confidence == DataConfidence.LOW:
        summary += " ⚠️ Low confidence (limited formal data in this area)."

    return MarketValueResult(
        fb_price=fb_price_monthly_pgk,
        suburb=suburb,
        property_type=property_type,
        benchmark_avg=round(adjusted_avg, 2),
        benchmark_median=round(adjusted_median, 2),
        benchmark_sample_size=stats.sample_size,
        benchmark_confidence=stats.benchmark_confidence if hasattr(stats, 'benchmark_confidence') else stats.confidence,
        label=label,
        pct_vs_avg=round(pct_vs_avg, 2),
        pct_vs_median=round(pct_vs_median, 2),
        summary=summary,
        recommendation=recommendation,
        deal_threshold_pct=deal_threshold,
        overpriced_threshold_pct=overpriced_threshold,
    )


# ── BATCH SCORER ─────────────────────────────────────────────────────────────

def score_listings_batch(listings: list[dict]) -> list[dict]:
    """
    Score a list of normalized listing dicts (output of normalizer.py).
    Adds 'market_value' key to each listing in-place.

    Args:
        listings: List of dicts with keys: price_pgk_monthly, suburb, property_type
    Returns:
        Same list with 'market_value' dict injected into each entry
    """
    for listing in listings:
        price = listing.get("price_pgk_monthly")
        suburb = listing.get("suburb") or ""
        p_type = listing.get("property_type")

        if price and suburb:
            result = score_market_value(price, suburb, p_type)
            listing["market_value"] = asdict(result)
        else:
            listing["market_value"] = {
                "label": MarketLabel.UNKNOWN,
                "summary": "Missing price or suburb data.",
                "pct_vs_avg": None,
            }
    return listings


# ── GET ALL SUBURB BENCHMARKS ─────────────────────────────────────────────────

def get_all_suburb_benchmarks() -> dict[str, dict]:
    """Return a summary of all suburbs for dashboard heatmap consumption."""
    result = {}
    for suburb_key in FORMAL_LISTINGS_DB:
        stats = compute_stats(FORMAL_LISTINGS_DB[suburb_key], suburb_key.title())
        result[suburb_key.title()] = {
            "avg_price": stats.avg_price,
            "median_price": stats.median_price,
            "std_dev": stats.std_dev,
            "sample_size": stats.sample_size,
            "min_price": stats.min_price,
            "max_price": stats.max_price,
            "confidence": stats.confidence.value,
        }
    return result


# ── TEST CASES ────────────────────────────────────────────────────────────────

TEST_CASES = [
    # (description, price, suburb, property_type)
    ("Cheap Boroko house — should be Deal",          1800, "Boroko",   "House"),
    ("Fair Boroko house",                            3100, "Boroko",   "House"),
    ("Overpriced Boroko house",                      5000, "Boroko",   "House"),
    ("Severely overpriced Waigani apartment",        9500, "Waigani",  "Apartment"),
    ("Strong deal Gerehu house",                      900, "Gerehu",   "House"),
    ("Fair Gordons apartment",                        5400, "Gordons",  "Apartment"),
    ("Room in Hohola — fair",                          600, "Hohola",   "Room"),
    ("Unknown suburb fallback",                       2500, "Moresby Hills", "House"),
    ("Missing property type",                         3200, "Boroko",   None),
]


def run_tests():
    print("=" * 72)
    print("Market Value Scoring Engine — Test Run")
    print("=" * 72)
    for label, price, suburb, p_type in TEST_CASES:
        result = score_market_value(price, suburb, p_type)
        print(f"\n[ {label} ]")
        print(f"  Input   : K{price:,}/mo · {suburb} · {p_type or 'type unknown'}")
        print(f"  Label   : {result.label.value}")
        print(f"  %vs Avg : {result.pct_vs_avg:+.1f}%" if result.pct_vs_avg is not None else "  %vs Avg : N/A")
        print(f"  Summary : {result.summary}")
    print("\n" + "=" * 72)

    print("\nAll suburb benchmarks (for dashboard):")
    benchmarks = get_all_suburb_benchmarks()
    print(json.dumps(benchmarks, indent=2))


if __name__ == "__main__":
    run_tests()
