import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import pytest
from png_scraper.valuation_engine import estimate_property_value

@pytest.fixture
def mock_listings():
    return [
        {
            "suburb": "Boroko",
            "property_type": "House",
            "is_for_sale": False,
            "price_monthly_k": 10000,
            "bedrooms": 3,
            "sqm": 800
        },
        {
            "suburb": "Boroko",
            "property_type": "Apartment",
            "is_for_sale": False,
            "price_monthly_k": 5000,
            "bedrooms": 2,
            "sqm": 120
        }
    ]

def test_sale_request_with_only_rent_data(mock_listings):
    # Request for SALE when only RENT data exists in suburb
    # It should match Listing 1 primarily
    res = estimate_property_value(mock_listings, "Boroko", "House", 3, 800, True)

    assert "error" not in res
    assert res["is_cross_category"] is True
    assert res["is_fallback"] is True
    # Rent 10k -> Sale = (10k * 12) / 0.08 = 1.5M
    # Weighted average will be slightly lower due to Match 2
    assert 1400000 < res["estimate"] < 1500001
    assert res["confidence"] <= 25

def test_rent_request_with_only_sale_data():
    mock_sale = [
        {
            "suburb": "Waigani",
            "property_type": "House",
            "is_for_sale": True,
            "price_monthly_k": 2000000,
            "bedrooms": 4,
            "sqm": 1000
        }
    ]
    # Request for RENT when only SALE data exists
    res = estimate_property_value(mock_sale, "Waigani", "House", 4, 1000, False)

    assert "error" not in res
    assert res["is_cross_category"] is True
    # Sale 2M -> Rent = (2M * 0.08) / 12 = 13333.33
    assert res["estimate"] == 13333
    assert res["confidence"] <= 25

def test_global_cross_category_fallback(mock_listings):
    # Request for SALE in "Gerehu" (not in mock) when only RENT data exists elsewhere (Boroko)
    res = estimate_property_value(mock_listings, "Gerehu", "House", 3, 800, True)

    assert "error" not in res
    assert res["is_cross_category"] is True
    assert res["is_fallback"] is True
    assert res["suburb"] == "National Average"
