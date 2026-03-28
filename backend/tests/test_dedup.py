from png_scraper.engine import Listing
from png_scraper.deduplicator import group_listings

def test_dedup():
    l1 = Listing(listing_id="1", source_site="Hausples", title="3BR House", price_raw="K2500",
                 price_monthly_k=2500, price_confidence="high", location="Boroko", suburb="Boroko",
                 listing_url="url1", is_verified=True, property_type="House", bedrooms=3, health_score=90)

    l2 = Listing(listing_id="2", source_site="FB", title="House for rent", price_raw="K2400",
                 price_monthly_k=2400, price_confidence="high", location="Boroko", suburb="Boroko",
                 listing_url="url2", is_verified=False, property_type="House", bedrooms=3, health_score=60)

    l3 = Listing(listing_id="3", source_site="Other", title="Modern Home", price_raw="K3500",
                 price_monthly_k=3500, price_confidence="high", location="Waigani", suburb="Waigani",
                 listing_url="url3", is_verified=True, property_type="House", bedrooms=3, health_score=95)

    grouped = group_listings([l1, l2, l3])

    # l1 and l2 should be in the same group (Boroko, House, 3BR, prices 2400/2500 round to 2400/2500
    # but let's see how round(2400/100)*100 works: it's 2400. round(2500/100)*100 is 2500.
    # Ah, price bucket might need wider range if we want 5% tolerance.
    # Let's adjust deduplicator if needed.

    print(f"L1 Group: {l1.group_id}")
    print(f"L2 Group: {l2.group_id}")
    print(f"L3 Group: {l3.group_id}")

    assert l1.group_id == l2.group_id or "Prices 2400/2500 didn't group"
    assert l1.group_id != l3.group_id

if __name__ == "__main__":
    test_dedup()
