import json
import sys
import os

# Add backend to path so we can import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.normalizer import calculate_health_score, check_verification
from png_scraper.b2b_engine import get_competitor_alerts, get_demand_forecast, get_lead_scoring

# 1. Test Trust Suite: Health Score
def test_health():
    print("Testing Health Score...")
    # calculate_health_score(price, suburb, p_type, beds, sqm, contacts, text)
    c1 = {"phones": []}
    c2 = {"phones": ["71234567"]}
    s1 = calculate_health_score(5000, None, None, None, None, c1, "Short") # Basic
    s2 = calculate_health_score(5000, "Waigani", "Apartment", 3, 150.0, c2, "Beautiful 3 Bedroom Apartment in Waigani with Pool and stuff")
    print(f"  Score 1: {s1}, Score 2: {s2}")
    assert s2 > s1
    assert s2 >= 90

# 2. Test Trust Suite: Verification
def test_verification():
    print("Testing Verification Logic...")
    v1 = check_verification({"phones": ["71234567"]}) # Mobile only
    v2 = check_verification({"phones": ["3214088"]})  # Landline
    v3 = check_verification({"phones": ["+675 320 0651"]}) # Registry match
    print(f"  V1 (Mobile): {v1}, V2 (Landline): {v2}, V3 (Registry): {v3}")
    assert v1 == False
    assert v2 == True
    assert v3 == True

# 3. Test B2B: Alerts Magnitude Check
def test_b2b_alerts():
    print("Testing B2B Alerts Magnitude Fix...")
    listings = [
        {"listing_id":"m1", "suburb":"W", "property_type":"A", "bedrooms":1, "price_monthly_k":1000000, "source_site":"Me", "is_for_sale":True},
        {"listing_id":"o1", "suburb":"W", "property_type":"A", "bedrooms":1, "price_monthly_k":3000, "source_site":"Other", "is_for_sale":True}
    ]
    alerts = get_competitor_alerts(listings, "Me")
    print(f"  Alerts (Huge Diff/Outlier): {len(alerts)}")
    assert len(alerts) == 0

    listings_2 = [
        {"listing_id":"m2", "suburb":"W", "property_type":"A", "bedrooms":1, "price_monthly_k":5000, "source_site":"Me", "is_for_sale":False},
        {"listing_id":"o2", "suburb":"W", "property_type":"A", "bedrooms":1, "price_monthly_k":4500, "source_site":"Other", "is_for_sale":False}
    ]
    alerts_2 = get_competitor_alerts(listings_2, "Me")
    print(f"  Alerts (Valid): {len(alerts_2)}")
    assert len(alerts_2) == 1

if __name__ == "__main__":
    try:
        test_health()
        test_verification()
        test_b2b_alerts()
        print("\n✅ All Backend Logic Tests Passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
