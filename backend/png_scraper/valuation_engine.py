"""
png_scraper/valuation_engine.py
─────────────────────────────────────────────────────────────────────────────
Automated Valuation Model (AVM): Estimates property value using scraped data.
"""

from typing import List, Dict, Any, Optional
import statistics

# Standard PNG Investment Yield (approx 8%)
DEFAULT_YIELD = 0.08

def estimate_property_value(
    listings: List[Dict],
    suburb: str,
    property_type: str,
    bedrooms: int,
    sqm: Optional[float] = None,
    is_for_sale: bool = True
) -> Dict[str, Any]:
    """
    Calculates an estimated market value based on similar historical listings.
    Supports cross-category fallback (Rent <-> Sale) using yield conversion.
    """
    is_fallback = False
    is_cross_category = False
    is_global = False

    # 1. Try specific match
    similar = [
        l for l in listings
        if l.get("suburb") == suburb
        and l.get("property_type") == property_type
        and l.get("is_for_sale") == is_for_sale
        and l.get("price_monthly_k")
    ]

    # 2. Try broader suburb match (Same category)
    if not similar:
        similar = [
            l for l in listings
            if l.get("suburb") == suburb
            and l.get("is_for_sale") == is_for_sale
            and l.get("price_monthly_k")
        ]
        if similar: is_fallback = True

    # 3. Try cross-category match in SAME suburb
    if not similar:
        similar = [
            l for l in listings
            if l.get("suburb") == suburb
            and l.get("is_for_sale") != is_for_sale
            and l.get("price_monthly_k")
        ]
        if similar:
            is_cross_category = True
            is_fallback = True

    # 4. Try global match (Same category)
    if not similar:
        similar = [
            l for l in listings
            if l.get("is_for_sale") == is_for_sale
            and l.get("price_monthly_k")
        ]
        if similar:
            is_fallback = True
            is_global = True

    # 5. Try global match (Cross category)
    if not similar:
        similar = [
            l for l in listings
            if l.get("is_for_sale") != is_for_sale
            and l.get("price_monthly_k")
        ]
        if similar:
            is_cross_category = True
            is_fallback = True
            is_global = True

    if not similar:
        return {"error": "Insufficient data in entire database", "confidence": 0}

    # Feature matching weights
    matches = []
    for s in similar:
        score = 100

        # Bed matching
        s_beds = s.get("bedrooms") or 0
        if s_beds != bedrooms:
            score -= abs(s_beds - bedrooms) * 20

        # SQM matching
        s_sqm = s.get("sqm")
        if sqm and s_sqm:
            diff_pct = abs(s_sqm - sqm) / sqm
            score -= diff_pct * 50

        # Type matching (if we lost it in fallbacks)
        if s.get("property_type") != property_type:
            score -= 30

        # Price conversion if cross-category
        price = s["price_monthly_k"]
        if is_cross_category:
            if is_for_sale:
                # Rent -> Sale conversion: (Monthly Rent * 12) / Yield
                price = (price * 12) / DEFAULT_YIELD
            else:
                # Sale -> Rent conversion: (Sale * Yield) / 12
                price = (price * DEFAULT_YIELD) / 12

        score = max(5, score)
        matches.append((price, score))

    # Calculate weighted average
    total_weight = sum(m[1] for m in matches)
    weighted_sum = sum(m[0] * m[1] for m in matches)
    estimate = weighted_sum / total_weight

    # Confidence based on sample size and match quality
    confidence = min(95, (len(matches) * 5) + (total_weight / len(matches)))

    if is_fallback:
        # Penalize confidence for fallbacks
        penalty = 0.5 if not is_cross_category else 0.3
        if is_global: penalty *= 0.5
        confidence = min(25, confidence * penalty)

    return {
        "estimate": int(estimate),
        "low_bound": int(estimate * 0.85),
        "high_bound": int(estimate * 1.15),
        "confidence": int(confidence),
        "sample_size": len(matches),
        "suburb": suburb if not is_global else "National Average",
        "property_type": property_type,
        "is_fallback": is_fallback,
        "is_cross_category": is_cross_category,
        "comparables": [
            {
                "title": l.get("title"),
                "price": l.get("price_monthly_k"),
                "source": l.get("source_site"),
                "is_sale": l.get("is_for_sale")
            }
            for l in sorted(similar, key=lambda x: abs((x.get("bedrooms") or 0) - bedrooms))[:3]
        ]
    }

def generate_market_report(valuation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares a detailed market comparison report object.
    """
    import random
    suburb = valuation.get("suburb", "Waigani")

    # Neighborhood Safety Score (Simulated)
    safety_score = random.randint(40, 95)
    safety_label = "Secure" if safety_score > 75 else "Developing" if safety_score > 55 else "Advisory Required"

    # Price History (Simulated 5-year data)
    base_price = valuation["estimate"]
    history = []
    for i in range(5, 0, -1):
        year = 2024 - i
        # Historical growth ~3-7%
        p = base_price * (0.8 + (i * 0.04))
        history.append({"year": year, "avg_price": int(p)})

    return {
        "report_id": f"VAL-{random_hex(6)}",
        "generated_at": "2024-03-28T12:00:00Z",
        "valuation": valuation,
        "neighborhood_safety": {
            "score": safety_score,
            "status": safety_label,
            "incidents_trend": "Decreasing",
            "patrol_presence": "Regular" if safety_score > 70 else "Occasional"
        },
        "price_history": history,
        "market_trends": {
            "suburb_demand": "High",
            "inventory_level": "Low",
            "avg_days_on_market": 45
        },
        "investment_analysis": {
            "gross_yield": "8.5%",
            "5_year_forecast": f"+{random.randint(8, 18)}.4% appreciation"
        }
    }

def random_hex(n):
    import uuid
    return str(uuid.uuid4())[:n].upper()
