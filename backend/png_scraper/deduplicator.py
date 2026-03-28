"""
png_scraper/deduplicator.py
─────────────────────────────────────────────────────────────────────────────
Deduplication & Multi-Agent Listing Grouping Engine
Identifies the same property listed by different agents or on multiple sites.
Uses fuzzy matching on suburb, price (within 5% tolerance), property type,
and bedrooms to assign a 'group_id' and 'duplicate_count'.
"""

import hashlib
import logging
from typing import List, Dict, Optional
from png_scraper.engine import Listing

log = logging.getLogger("png_scraper.dedup")

def calculate_fuzzy_key(listing: Listing) -> Optional[str]:
    """
    Creates a semantic key for fuzzy matching.
    Key: Suburb | PropertyType | Bedrooms | Price (bucketed by ~10% tolerance)
    """
    sub = (listing.suburb or "Unknown").lower().strip()
    ptype = (listing.property_type or "Unknown").lower().strip()
    beds = str(listing.bedrooms or 0)

    price = listing.price_monthly_k or 0

    # Using a logarithmic bucket for price to allow wider tolerance on high prices
    # e.g. 500 PGK diff on K10,000 is 5%, but on K1,000 it is 50%.
    # For PNG, we'll use a 250 PGK bucket for rent < 5000, 1000 PGK bucket for > 5000.
    if price < 5000:
        price_bucket = str(round(price / 250) * 250)
    else:
        price_bucket = str(round(price / 1000) * 1000)

    if sub == "unknown" and price == 0:
        return None

    raw_key = f"{sub}|{ptype}|{beds}|{price_bucket}"
    return hashlib.md5(raw_key.encode()).hexdigest()[:12]

def group_listings(listings: List[Listing]) -> List[Listing]:
    """
    Groups listings by fuzzy key and assigns a group_id.
    Sorts each group so the most 'trusted' (verified, high health score)
    listing appears as the primary representative if needed.
    """
    groups: Dict[str, List[Listing]] = {}

    for lst in listings:
        key = calculate_fuzzy_key(lst)
        if not key:
            continue

        if key not in groups:
            groups[key] = []
        groups[key].append(lst)

    processed: List[Listing] = []

    for key, items in groups.items():
        # If group has more than 1 item, it's a suspected duplicate
        group_id = f"grp_{key}"

        # Sort items in group: Verified first, then by health_score desc
        items.sort(key=lambda x: (x.is_verified, x.health_score), reverse=True)

        for i, item in enumerate(items):
            item.group_id = group_id
            # We can also attach meta-info about the group to the primary item
            # or to all items for the UI to consume.
            processed.append(item)

    # Add back listings that weren't grouped (if any, though calculate_fuzzy_key usually returns something)
    grouped_ids = {l.listing_id for l in processed}
    for l in listings:
        if l.listing_id not in grouped_ids:
            processed.append(l)

    return processed

def get_duplicates_summary(listings: List[Listing]) -> Dict:
    """Returns statistics about duplicate listings found."""
    groups = {}
    for l in listings:
        if l.group_id:
            groups[l.group_id] = groups.get(l.group_id, 0) + 1

    duplicates = [count for count in groups.values() if count > 1]
    return {
        "total_groups": len(groups),
        "total_duplicates": sum(duplicates),
        "duplicate_listings_count": len(duplicates),
        "max_group_size": max(duplicates) if duplicates else 0
    }
