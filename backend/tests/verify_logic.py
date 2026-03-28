from png_scraper.b2b_engine import get_competitor_alerts

listings = [
    {
        "listing_id": "mine-1",
        "title": "1 Bedroom Studio - Waigani",
        "suburb": "Waigani",
        "property_type": "Studio",
        "bedrooms": 1,
        "price_monthly_k": 707520,
        "source_site": "SRE PNG",
        "is_for_sale": True
    },
    {
        "listing_id": "other-1",
        "title": "Cheap Rental",
        "suburb": "Waigani",
        "property_type": "Studio",
        "bedrooms": 1,
        "price_monthly_k": 5474,
        "source_site": "Century 21 PNG",
        "is_for_sale": False # Different!
    },
    {
        "listing_id": "other-2",
        "title": "Another Rental",
        "suburb": "Waigani",
        "property_type": "Studio",
        "bedrooms": 1,
        "price_monthly_k": 5891,
        "source_site": "Hausples",
        "is_for_sale": True # Same! But huge price diff
    }
]

alerts = get_competitor_alerts(listings, "SRE PNG")
import json
print(json.dumps(alerts, indent=2))
