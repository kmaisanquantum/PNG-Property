import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.valuation_engine import estimate_property_value

def test_valuation_logic():
    print("Testing Valuation Engine Logic...")

    # Mock listings
    listings = [
        {"suburb": "Waigani", "property_type": "House", "bedrooms": 3, "sqm": 200, "price_monthly_k": 800000, "is_for_sale": True},
        {"suburb": "Waigani", "property_type": "House", "bedrooms": 3, "sqm": 220, "price_monthly_k": 850000, "is_for_sale": True},
        {"suburb": "Waigani", "property_type": "House", "bedrooms": 4, "sqm": 300, "price_monthly_k": 1200000, "is_for_sale": True},
        {"suburb": "Boroko", "property_type": "Apartment", "bedrooms": 2, "sqm": 100, "price_monthly_k": 450000, "is_for_sale": True}
    ]

    # Test case 1: Exact match suburb/type/beds
    res = estimate_property_value(listings, "Waigani", "House", 3, 210, True)
    print(f"  Estimate (3br Waigani): K{res['estimate']:,} (Conf: {res['confidence']}%)")
    assert 800000 < res["estimate"] < 1000000
    assert res["confidence"] > 50

    # Test case 2: Data poor fallback
    res2 = estimate_property_value(listings, "Waigani", "Studio", 1, 50, True)
    print(f"  Fallback Estimate: K{res2['estimate']:,}")
    assert res2["estimate"] > 0

    # Test case 3: Global fallback for missing suburb
    res3 = estimate_property_value(listings, "Gerehu", "House", 3, 200, True)
    print(f"  Global fallback: {res3.get('suburb')}, Confidence: {res3.get('confidence')}%")
    assert res3["suburb"] == "National Average"
    assert res3["is_fallback"] is True
    assert res3["confidence"] <= 20

if __name__ == "__main__":
    try:
        test_valuation_logic()
        print("\n✅ Valuation Engine Verified!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
