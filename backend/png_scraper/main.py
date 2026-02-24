"""
png_scraper/main.py
─────────────────────────────────────────────────────────────────────────────
PNG Real Estate Scraper — Main Orchestrator

Runs all scraper classes in parallel (with concurrency cap),
deduplicates the unified dataset, and exports JSON + CSV.

Usage:
    python -m png_scraper.main                   # all sources, headless
    python -m png_scraper.main --no-fb           # skip Facebook
    python -m png_scraper.main --visible         # show browser windows
    python -m png_scraper.main --sources hausples professionals
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from png_scraper.engine import Listing, log
from png_scraper.scrapers.hausples       import HausplesScraper
from png_scraper.scrapers.professionals  import ProfessionalsScraper
from png_scraper.scrapers.general_agency import GeneralAgencyScraper, AGENCY_CONFIGS
from png_scraper.scrapers.facebook       import FacebookScraper

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ── deduplication ─────────────────────────────────────────────────────────────

def deduplicate(listings: list[Listing]) -> list[Listing]:
    """
    Remove duplicates. Priority: agency listings beat social listings.
    Key = (suburb, price_monthly_k, property_type, bedrooms) — fuzzy match.
    """
    seen_ids:    dict[str, Listing] = {}    # listing_id (exact)
    seen_fuzzy:  dict[str, Listing] = {}    # semantic key (near-duplicate)
    unique: list[Listing] = []

    for lst in listings:
        # Exact dedup by URL-hash id
        if lst.listing_id in seen_ids:
            continue
        seen_ids[lst.listing_id] = lst

        # Fuzzy dedup
        fuzzy_key = (
            (lst.suburb or "").lower(),
            lst.price_monthly_k,
            (lst.property_type or "").lower(),
            lst.bedrooms,
        )
        if fuzzy_key in seen_fuzzy:
            existing = seen_fuzzy[fuzzy_key]
            # Keep the verified/agency listing, discard social duplicate
            if lst.is_verified and not existing.is_verified:
                seen_fuzzy[fuzzy_key] = lst
                unique = [l for l in unique if l.listing_id != existing.listing_id]
                unique.append(lst)
            continue

        seen_fuzzy[fuzzy_key] = lst
        unique.append(lst)

    return unique


# ── export helpers ────────────────────────────────────────────────────────────

def export_json(listings: list[Listing], path: Path) -> None:
    data = [l.to_dict() for l in listings]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"JSON → {path}  ({len(data)} records)")


def export_csv(listings: list[Listing], path: Path) -> None:
    if not listings:
        return
    fields = list(listings[0].to_dict().keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(l.to_dict() for l in listings)
    log.info(f"CSV  → {path}  ({len(listings)} records)")


def print_summary(listings: list[Listing]) -> None:
    from collections import Counter
    print("\n" + "═" * 60)
    print("  PNG REAL ESTATE SCRAPER — FINAL SUMMARY")
    print("═" * 60)
    print(f"  Total listings (post-dedup)  : {len(listings)}")
    by_source = Counter(l.source_site for l in listings)
    print(f"\n  By source:")
    for src, n in sorted(by_source.items(), key=lambda x: -x[1]):
        verified = "✓" if any(l.is_verified for l in listings if l.source_site == src) else "~"
        print(f"    {verified}  {src:<30} {n:>4}")
    by_suburb = Counter(l.suburb for l in listings if l.suburb)
    print(f"\n  Top suburbs:")
    for suburb, n in by_suburb.most_common(8):
        print(f"    {suburb:<25} {n:>4} listings")
    priced = [l.price_monthly_k for l in listings if l.price_monthly_k]
    if priced:
        print(f"\n  Price range  : K{min(priced):,} – K{max(priced):,} / month")
        print(f"  Average rent : K{int(sum(priced)/len(priced)):,} / month")
    print("═" * 60 + "\n")


# ── orchestrator ──────────────────────────────────────────────────────────────

async def run_all(
    include_facebook: bool = True,
    headless: bool = True,
    sources: list[str] = None,
    max_pages: int = 5,
    agency_concurrency: int = 3,
) -> list[Listing]:
    """
    Orchestrate all scrapers with a concurrency cap.

    Args:
        include_facebook:    Include Facebook Marketplace scraper
        headless:            Run browsers headless
        sources:             Whitelist of scraper names (None = all)
        max_pages:           Pages per portal scraper
        agency_concurrency:  Parallel agency scrapers

    Returns:
        Unified, deduplicated list[Listing]
    """
    all_results: list[Listing] = []
    tasks = []

    def _want(name: str) -> bool:
        return sources is None or name.lower() in [s.lower() for s in sources]

    # ── portals ────────────────────────────────────────────────────────────
    if _want("hausples"):
        tasks.append(HausplesScraper(max_pages=max_pages, headless=headless).run())

    if _want("professionals"):
        tasks.append(ProfessionalsScraper(max_pages=max_pages, headless=headless).run())

    # ── agency sites (batched with semaphore) ─────────────────────────────
    sem = asyncio.Semaphore(agency_concurrency)
    async def _agency(cfg):
        async with sem:
            if not _want(cfg.source_site) and not _want("agencies"):
                return []
            return await GeneralAgencyScraper(cfg, headless=headless).run()

    for cfg in AGENCY_CONFIGS:
        tasks.append(_agency(cfg))

    # ── Facebook ────────────────────────────────────────────────────────────
    if include_facebook and _want("facebook"):
        tasks.append(FacebookScraper(scroll_rounds=8, headless=headless).run())

    # ── run all ─────────────────────────────────────────────────────────────
    log.info(f"Launching {len(tasks)} scrapers...")
    t0 = time.perf_counter()

    batches = await asyncio.gather(*tasks, return_exceptions=True)
    for batch in batches:
        if isinstance(batch, Exception):
            log.error(f"Scraper error: {batch}")
        elif isinstance(batch, list):
            all_results.extend(batch)

    elapsed = time.perf_counter() - t0
    log.info(f"All scrapers complete in {elapsed:.1f}s. Raw total: {len(all_results)}")

    # ── deduplicate ──────────────────────────────────────────────────────────
    unified = deduplicate(all_results)
    log.info(f"After dedup: {len(unified)} unique listings ({len(all_results)-len(unified)} removed)")

    return unified


# ── CLI entry point ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PNG Real Estate Scraper")
    p.add_argument("--no-fb",    action="store_true",       help="Skip Facebook Marketplace")
    p.add_argument("--visible",  action="store_true",       help="Show browser windows")
    p.add_argument("--pages",    type=int, default=5,       help="Pages per scraper (default 5)")
    p.add_argument("--concurrency", type=int, default=3,   help="Parallel agency scrapers (default 3)")
    p.add_argument("--sources",  nargs="*",                 help="Whitelist scrapers by name")
    p.add_argument("--out-dir",  default="output",          help="Output directory (default ./output)")
    return p.parse_args()


async def main_async(args: argparse.Namespace) -> list[dict]:
    global OUTPUT_DIR
    OUTPUT_DIR = Path(args.out_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    listings = await run_all(
        include_facebook   = not args.no_fb,
        headless           = not args.visible,
        sources            = args.sources,
        max_pages          = args.pages,
        agency_concurrency = args.concurrency,
    )

    # ── export ────────────────────────────────────────────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_json(listings, OUTPUT_DIR / f"png_listings_{ts}.json")
    export_csv (listings, OUTPUT_DIR / f"png_listings_{ts}.csv")

    # Always write a "latest" file for the dashboard to consume
    export_json(listings, OUTPUT_DIR / "png_listings_latest.json")
    export_csv (listings, OUTPUT_DIR / "png_listings_latest.csv")

    print_summary(listings)

    # Return as list of dicts for programmatic / analytics use
    return [l.to_dict() for l in listings]


def main():
    args = parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
