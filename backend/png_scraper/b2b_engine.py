"""
png_scraper/b2b_engine.py
─────────────────────────────────────────────────────────────────────────────
B2B Intelligence Engine: Competitor Analysis, Demand Forecasting & Lead Scoring.
"""

from typing import List, Dict, Any
from collections import defaultdict
import random

def get_competitor_alerts(listings: List[Dict], agent_name: str) -> List[Dict]:
    """
    Find listings from other sources that are similar to the agent's listings
    but priced lower (Competitor Pricing Alerts).
    """
    alerts = []
    my_listings = [l for l in listings if agent_name.lower() in (l.get("source_site") or "").lower()]
    others = [l for l in listings if agent_name.lower() not in (l.get("source_site") or "").lower()]

    for mine in my_listings:
        sub = mine.get("suburb")
        ptype = mine.get("property_type")
        beds = mine.get("bedrooms")
        my_price = mine.get("price_monthly_k")

        if not all([sub, ptype, beds, my_price]): continue

        # Look for cheaper alternatives
        cheaper = []
        for other in others:
            if (other.get("suburb") == sub and
                other.get("property_type") == ptype and
                other.get("bedrooms") == beds and
                other.get("is_for_sale") == mine.get("is_for_sale")):

                other_price = other.get("price_monthly_k")
                if other_price and other_price < my_price:
                    # Avoid comparing rental prices to sale prices (different magnitudes)
                    if (my_price / other_price) > 50 or (other_price / my_price) > 50:
                        continue

                    cheaper.append({
                        "id": other.get("listing_id"),
                        "source": other.get("source_site"),
                        "price": other_price,
                        "diff": my_price - other_price,
                        "pct": round(((my_price - other_price) / my_price) * 100, 1)
                    })

        if cheaper:
            # Sort by biggest discount
            cheaper.sort(key=lambda x: x["diff"], reverse=True)
            alerts.append({
                "my_listing": {
                    "id": mine.get("listing_id"),
                    "title": mine.get("title"),
                    "price": my_price
                },
                "competitors": cheaper[:3] # Top 3 biggest threats
            })

    return alerts

def get_demand_forecast(listings: List[Dict]) -> List[Dict]:
    """
    Identify Supply-Demand Gaps.
    Transform raw listing counts into "Market Gaps" using simulated search spikes.
    """
    suburbs = list(set(l["suburb"] for l in listings if l.get("suburb")))
    types = ["Apartment", "House", "Townhouse", "Studio"]

    # Calculate Supply
    supply = defaultdict(int)
    for l in listings:
        key = (l.get("suburb"), l.get("property_type"))
        if all(key): supply[key] += 1

    rng = random.Random(42) # Consistent mock spikes
    forecast = []

    for sub in suburbs:
        for t in types:
            s_count = supply[(sub, t)]

            # Simulate Demand: Base demand + random spike
            # (In production, this would come from search logs / clickstream)
            base_demand = rng.randint(5, 50)
            spike = rng.randint(0, 30) if rng.random() > 0.7 else 0
            demand_index = base_demand + spike

            gap = demand_index - s_count
            if gap > 5: # Only report significant opportunities
                forecast.append({
                    "suburb": sub,
                    "property_type": t,
                    "supply": s_count,
                    "demand_index": demand_index,
                    "spike_pct": round((spike / base_demand) * 100) if spike else 0,
                    "opportunity_score": min(100, gap * 2)
                })

    return sorted(forecast, key=lambda x: x["opportunity_score"], reverse=True)

def get_lead_scoring() -> List[Dict]:
    """
    Identify 'Hot' leads based on simulated interaction patterns.
    """
    names = ["John Mara", "Sarah Gari", "Dixon Tau", "Michael Kila", "Anna Somare", "James Kopi"]
    suburbs = ["Waigani", "Boroko", "Gerehu", "Eight Mile"]

    leads = []
    rng = random.Random(88)

    for i, name in enumerate(names):
        views = rng.randint(3, 15)
        repeat_visits = rng.randint(1, 6)
        saved_listings = rng.randint(0, 3)

        # Lead score formula
        score = (views * 5) + (repeat_visits * 15) + (saved_listings * 25)

        leads.append({
            "lead_id": f"lead_{i}",
            "name": name,
            "interest": rng.choice(suburbs),
            "price_range": f"K{rng.randint(2,5)}k - K{rng.randint(6,10)}k",
            "score": min(100, score),
            "status": "Hot" if score > 70 else "Warm" if score > 40 else "Cool",
            "last_active": "2 hours ago" if rng.random() > 0.5 else "Yesterday",
            "interactions": {
                "total_views": views,
                "repeat_visits": repeat_visits,
                "saved": saved_listings
            }
        })

    return sorted(leads, key=lambda x: x["score"], reverse=True)
