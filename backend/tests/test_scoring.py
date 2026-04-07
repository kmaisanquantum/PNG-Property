import pytest
from datetime import datetime, timezone, timedelta
from services.scoring_engine import calculate_investment_score, haversine

def test_haversine():
    # Distance from Waigani to Boroko (roughly)
    # Waigani: -9.4224, 147.1831
    # Boroko: -9.4723, 147.2000
    dist = haversine(-9.4224, 147.1831, -9.4723, 147.2000)
    assert 5.0 < dist < 6.5

def test_investment_score_price_ratio():
    # Case 1: Price is half the market average (should get full 40 pts for price)
    # Proximity and days will be neutral (20 + 10)
    # Total ~ 40 + 20 + 10 = 70
    score, flags = calculate_investment_score(
        price=1000,
        market_avg=2000,
        lat=None,
        lng=None,
        first_seen_at=datetime.now(timezone.utc).isoformat()
    )
    assert score >= 60.0

def test_investment_score_proximity():
    # Case 2: Near Waigani Central Hub (lat: -9.4224, lng: 147.1831)
    # Price ratio neutral (20), days neutral (10)
    # Proximity should be high (~40)
    # Total ~ 20 + 40 + 10 = 70
    score, flags = calculate_investment_score(
        price=None,
        market_avg=None,
        lat=-9.4225,
        lng=147.1832,
        first_seen_at=datetime.now(timezone.utc).isoformat()
    )
    assert score >= 60.0

def test_investment_score_stale_listing():
    # Case 3: Listing > 90 days old
    # Price/Proximity neutral (20 + 20 = 40)
    # Days score should be max (20) + "High Negotiation" flag
    # Total ~ 40 + 20 = 60
    old_date = (datetime.now(timezone.utc) - timedelta(days=95)).isoformat()
    score, flags = calculate_investment_score(
        price=None,
        market_avg=None,
        lat=None,
        lng=None,
        first_seen_at=old_date
    )
    assert "High Negotiation" in flags
    assert score >= 55.0

def test_investment_score_bad_deal():
    # Case 4: Overpriced, Far away, New listing
    # Price ratio 1.5x (0 pts)
    # Distance 20km from any hub (0 pts)
    # Days 0 (0 pts)
    # Total = 0
    score, flags = calculate_investment_score(
        price=3000,
        market_avg=2000,
        lat=-9.6, # Far south
        lng=147.4, # Far east
        first_seen_at=datetime.now(timezone.utc).isoformat()
    )
    assert score < 10.0
