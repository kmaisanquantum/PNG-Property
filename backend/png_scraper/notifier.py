"""
png_scraper/notifier.py
─────────────────────────────────────────────────────────────────────────────
Notification Engine: Detects Price Drops and New Listings.
Simulates WhatsApp & Messenger delivery for data-light social plan users.
"""

import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger("notifier")

def detect_price_drops(old_listings: List[Dict], new_listings: List[Dict]) -> List[Dict]:
    """
    Compare old and new listings to find price reductions on the same property.
    """
    old_map = {l["listing_id"]: l for l in old_listings if l.get("price_monthly_k")}
    drops = []

    for nl in new_listings:
        lid = nl.get("listing_id")
        if lid in old_map:
            old_price = old_map[lid].get("price_monthly_k")
            new_price = nl.get("price_monthly_k")

            if new_price and old_price and new_price < old_price:
                pct = round(((old_price - new_price) / old_price) * 100, 1)
                drops.append({
                    "listing_id": lid,
                    "title": nl.get("title"),
                    "old_price": old_price,
                    "new_price": new_price,
                    "drop_pct": pct,
                    "url": nl.get("listing_url")
                })
    return drops

def match_saved_searches(new_listings: List[Dict], saved_searches: List[Dict]) -> List[Dict]:
    """
    Find new listings that match a user's 'Followed Search' criteria.
    """
    matches = []
    for search in saved_searches:
        criteria = search.get("criteria", {})
        suburb = criteria.get("suburb")
        ptype = criteria.get("type")
        max_p = criteria.get("max_price")

        for nl in new_listings:
            # Simple matching logic
            if suburb and nl.get("suburb") != suburb: continue
            if ptype and nl.get("property_type") != ptype: continue
            if max_p and (nl.get("price_monthly_k") or 0) > max_p: continue

            matches.append({
                "user_id": search.get("user_id"),
                "search_name": search.get("name"),
                "listing": nl
            })
    return matches

def send_whatsapp_alert(phone: str, message: str):
    """
    Simulated WhatsApp API call (e.g., via Twilio or Meta Graph API).
    Logs the alert as a surrogate for actual delivery in this sandbox.
    """
    log.info(f"[WHATSAPP ALERT] To: {phone} | Message: {message}")
    # In a real app:
    # client.messages.create(body=message, from_='whatsapp:+123', to=f'whatsapp:{phone}')
    return True

def notify_price_drop(user_phone: str, drop: Dict):
    msg = (
        f"🔥 PRICE DROP ALERT!\n"
        f"Property: {drop['title']}\n"
        f"Was: K{drop['old_price']:,} -> Now: K{drop['new_price']:,} (-{drop['drop_pct']}%)\n"
        f"View: {drop['url']}"
    )
    return send_whatsapp_alert(user_phone, msg)

def notify_new_match(user_phone: str, search_name: str, listing: Dict):
    msg = (
        f"🔔 NEW MATCH for '{search_name}'\n"
        f"Property: {listing['title']}\n"
        f"Price: K{listing.get('price_monthly_k', 0):,}\n"
        f"Suburb: {listing.get('suburb')}\n"
        f"View: {listing.get('listing_url')}"
    )
    return send_whatsapp_alert(user_phone, msg)
