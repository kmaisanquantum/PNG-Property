
from main import _load_listings, _mock_listings
from png_scraper.b2b_engine import get_competitor_alerts, get_demand_forecast, get_lead_scoring
import json

def debug_b2b():
    listings = _load_listings()
    print(f"Total listings: {len(listings)}")

    agent = "The Professionals"
    alerts = get_competitor_alerts(listings, agent)
    print(f"Alerts for {agent}: {len(alerts)}")

    forecast = get_demand_forecast(listings)
    print(f"Forecast items: {len(forecast)}")

    leads = get_lead_scoring()
    print(f"Leads: {len(leads)}")

    # Check if 'The Professionals' exists in listings
    sources = set(l.get("source_site") for l in listings)
    print(f"Sources found: {sources}")

if __name__ == "__main__":
    debug_b2b()
