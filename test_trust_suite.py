from png_scraper.normalizer import normalize
from png_scraper.engine import make_listing

def test_normalizer():
    print("Testing Normalizer...")
    raw = "3bdrm house in Boroko. K500 per week. Call 71234567. Trusted landlord."
    res = normalize(raw)
    print(f"Health Score: {res.get('health_score')}")
    print(f"Is Verified: {res.get('is_verified')}")
    assert 'health_score' in res
    assert 'is_verified' in res

def test_engine_factory():
    print("\nTesting Engine Factory...")
    lst = make_listing(
        source_site="Facebook",
        title="3BR House",
        price_raw="K500/week",
        location="Boroko",
        listing_url="http://fb.com/1",
        is_verified=False,
        raw_text="3bdrm house in Boroko. Call 321 4088." # Trusted landline
    )
    print(f"Listing ID: {lst.listing_id}")
    print(f"Health Score: {lst.health_score}")
    print(f"Is Verified: {lst.is_verified}")
    print(f"Is Middleman: {lst.is_middleman}")
    assert lst.health_score > 0
    assert lst.is_verified is True # Should be verified by landline

if __name__ == "__main__":
    try:
        test_normalizer()
        test_engine_factory()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
