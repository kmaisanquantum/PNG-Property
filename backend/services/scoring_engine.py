import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone

# Planned 'Safe-Link' Hubs (Placeholder coordinates for Port Moresby)
SAFELINK_HUBS = [
    {"name": "Waigani Central Hub", "lat": -9.4224, "lng": 147.1831},
    {"name": "Boroko Gateway Hub", "lat": -9.4723, "lng": 147.2000},
    {"name": "Town Waterfront Hub", "lat": -9.4750, "lng": 147.1450},
]

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    R = 6371.0  # Radius of the Earth in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_investment_score(
    price: Optional[float],
    market_avg: Optional[float],
    lat: Optional[float],
    lng: Optional[float],
    first_seen_at: str
) -> Tuple[float, List[str]]:
    """
    Calculates the 'DSPNG Investment Score' (0-100).
    Weights:
    - Price-to-market ratio (40%)
    - Proximity to Safe-Link hubs (40%)
    - Days on Market / Negotiation potential (20%)
    """
    score = 0.0
    flags = []

    # 1. Price-to-market ratio (40 points)
    if price and market_avg and market_avg > 0:
        ratio = price / market_avg
        # If price is 50% of market avg or less, get full 40 points
        # If price is 150% of market avg or more, get 0 points
        price_score = max(0, min(40, (1.5 - ratio) * 40))
        score += price_score
    else:
        # Neutral if data missing
        score += 20

    # 2. Proximity to Safe-Link hubs (40 points)
    if lat is not None and lng is not None:
        distances = [haversine(lat, lng, hub["lat"], hub["lng"]) for hub in SAFELINK_HUBS]
        min_dist = min(distances)
        # 100% score (40 pts) if within 1km, 0 score if > 10km
        proximity_score = max(0, min(40, (10 - min_dist) / 9 * 40))
        score += proximity_score
    else:
        # Neutral if data missing
        score += 20

    # 3. Days on Market (20 points)
    try:
        seen_date = datetime.fromisoformat(first_seen_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days_on_market = (now - seen_date).days

        if days_on_market > 90:
            flags.append("High Negotiation")
            # Older listings might be more negotiable = better investment opportunity?
            # Or they might be "stale". For this engine, we'll favor high days as opportunity.
            score += 20
        else:
            # Linear scale for newer listings
            score += min(20, (days_on_market / 90) * 20)
    except Exception:
        score += 10

    return round(max(0, min(100, score)), 1), flags
