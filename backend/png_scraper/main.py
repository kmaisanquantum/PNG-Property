"""
png_scraper/main.py
─────────────────────────────────────────────────────────────────────────────
PNG Real Estate Scraper — Main Orchestrator

Runs all scraper classes in parallel (with concurrency cap),
deduplicates the unified dataset, and exports JSON + CSV.
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
from typing import Optional, Callable, Any

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

    # Sort so that verified/agency listings come first - helps the fuzzy dedup
    # prioritize high-quality data.
    sorted_listings = sorted(listings, key=lambda l: (not l.is_verified, l.source_site))

    for lst in sorted_listings:
        # 1. Exact dedup by listing_id
        if lst.listing_id in seen_ids:
            continue
        seen_ids[lst.listing_id] = lst

        # 2. Fuzzy dedup (Semantic matching)
        # We only fuzzy dedup if we have enough identifying info
        if lst.suburb and lst.price_monthly_k and lst.property_type:
            fuzzy_key = (
                str(lst.suburb).lower().strip(),
                int(lst.price_monthly_k),
                str(lst.property_type).lower().strip(),
                int(lst.bedrooms or 0)
            )

            if fuzzy_key in seen_fuzzy:
                existing = seen_fuzzy[fuzzy_key]
                # If current is verified and existing is not, replace it
                if lst.is_verified and not existing.is_verified:
                    seen_fuzzy[fuzzy_key] = lst
                    # Replace in unique list
                    unique = [l for l in unique if l.listing_id != existing.listing_id]
                    unique.append(lst)
                # Otherwise, if we already have a verified one, or the existing one
                # is from a primary portal, skip the new one.
                continue

            seen_fuzzy[fuzzy_key] = lst

        unique.append(lst)

    return unique


# ── export helpers ────────────────────────────────────────────────────────────

def export_json(listings: list[Listing], path: Path) -> None:
    data = [l.to_dict() if hasattr(l, "to_dict") else l for l in listings]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"JSON → {path}  ({len(data)} records)")


def export_csv(listings: list[Listing], path: Path) -> None:
    if not listings:
        return
    # Ensure we use dicts for CSV export
    dicts = [l.to_dict() if hasattr(l, "to_dict") else l for l in listings]
    fields = list(dicts[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dicts)
    log.info(f"CSV  → {path}  ({len(listings)} records)")


# ── orchestrator ──────────────────────────────────────────────────────────────

async def run_all(
    include_facebook: bool = False,
    headless: bool = True,
    sources: list[str] = None,
    max_pages: int = 5,
    agency_concurrency: int = 2,
    on_progress: Optional[Callable[[str, int, float], Any]] = None,
) -> list[Listing]:
    all_results: list[Listing] = []
    instance_tasks: list[tuple[str, Any]] = []

    def _want(name: str) -> bool:
        if not sources: return True
        low_sources = [s.lower() for s in sources]
        low_name = name.lower()

        # Direct name match (partial)
        if any(s in low_name for s in low_sources): return True

        # Categories
        portals = ["hausples", "png real estate", "png buy n rent", "professionals", "the professionals"]
        if "portals" in low_sources and low_name in portals: return True

        # 'agencies' excludes portals and social media
        if "agencies" in low_sources:
            if low_name not in portals and "facebook" not in low_name:
                return True

        return False

    # 1. Portals
    if _want("hausples"):
        instance_tasks.append(("Hausples Rent", HausplesScraper(max_pages=max_pages, headless=headless, mode="rent")))
        instance_tasks.append(("Hausples Sale", HausplesScraper(max_pages=max_pages, headless=headless, mode="sale")))

    if _want("png real estate"):
        instance_tasks.append(("PNG Real Estate Rent", HausplesScraper(
            base_url="https://www.pngrealestate.com.pg", source_site="PNG Real Estate",
            max_pages=max_pages, headless=headless, mode="rent"
        )))
        instance_tasks.append(("PNG Real Estate Sale", HausplesScraper(
            base_url="https://www.pngrealestate.com.pg", source_site="PNG Real Estate",
            max_pages=max_pages, headless=headless, mode="sale"
        )))

    if _want("png buy n rent"):
        instance_tasks.append(("PNG Buy n Rent Rent", HausplesScraper(
            base_url="https://www.pngbuynrent.com", source_site="PNG Buy n Rent",
            max_pages=max_pages, headless=headless, mode="rent"
        )))
        instance_tasks.append(("PNG Buy n Rent Sale", HausplesScraper(
            base_url="https://www.pngbuynrent.com", source_site="PNG Buy n Rent",
            max_pages=max_pages, headless=headless, mode="sale"
        )))

    if _want("professionals"):
        instance_tasks.append(("The Professionals", ProfessionalsScraper(max_pages=max_pages, headless=headless)))

    # 2. Agency Sites
    for cfg in AGENCY_CONFIGS:
        if _want(cfg.source_site):
            instance_tasks.append((cfg.source_site, GeneralAgencyScraper(cfg, headless=headless)))

    # 3. Facebook
    if include_facebook or _want("facebook"):
        instance_tasks.append(("Facebook Marketplace", FacebookScraper(scroll_rounds=10, headless=headless)))

    if not instance_tasks:
        log.warning("No scrapers selected based on 'sources' filter.")
        return []

    log.info(f"Launching {len(instance_tasks)} tasks (concurrency={agency_concurrency})...")

    sem = asyncio.Semaphore(agency_concurrency)
    completed = 0
    total = len(instance_tasks)

    async def _run_task(name, inst):
        nonlocal completed
        async with sem:
            try:
                def _sub_prog(count, page):
                    if on_progress:
                        # Estimate total progress based on completed tasks + current task fraction
                        prog = (completed / total) * 100
                        on_progress(name, count, prog)

                res = await inst.run(on_progress=_sub_prog)
                completed += 1
                if on_progress: on_progress(name, 0, (completed / total) * 100)
                return res
            except Exception as e:
                log.error(f"[{name}] Task failed: {e}")
                completed += 1
                return []

    batches = await asyncio.gather(*[_run_task(n, i) for n, i in instance_tasks])
    for b in batches:
        if isinstance(b, list): all_results.extend(b)

    log.info(f"Scrape finished. Raw total: {len(all_results)}")

    unified = deduplicate(all_results)
    log.info(f"After dedup: {len(unified)} unique listings ({len(all_results)-len(unified)} removed)")

    return unified

async def main_async():
    # Simple CLI fallback
    results = await run_all(include_facebook=True, max_pages=2)
    export_json(results, OUTPUT_DIR / "png_listings_latest.json")

if __name__ == "__main__":
    asyncio.run(main_async())
