
from png_scraper.b2b_engine import get_competitor_alerts, get_demand_forecast, get_lead_scoring
from main import _mock_listings

def test_b2b_engine():
    listings = _mock_listings()

    # 1. Test Competitor Alerts
    alerts = get_competitor_alerts(listings, "The Professionals")
    print(f"Competitor Alerts: {len(alerts)} items found.")
    if alerts:
        print(f"Sample Alert: {alerts[0]['my_listing']['title']} has {len(alerts[0]['competitors'])} threats.")

    # 2. Test Demand Forecasting
    forecast = get_demand_forecast(listings)
    print(f"Demand Forecast: {len(forecast)} opportunities found.")
    if forecast:
        print(f"Top Opportunity: {forecast[0]['suburb']} {forecast[0]['property_type']} (Score: {forecast[0]['opportunity_score']})")

    # 3. Test Lead Scoring
    leads = get_lead_scoring()
    print(f"Lead Scoring: {len(leads)} leads identified.")
    if leads:
        print(f"Top Lead: {leads[0]['name']} (Score: {leads[0]['score']})")

if __name__ == "__main__":
    test_b2b_engine()
