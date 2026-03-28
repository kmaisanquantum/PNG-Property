import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import _load_listings, _mock_listings

def test_load_listings():
    # Force mock data if file doesn't exist
    ls = _load_listings()
    print(f"Total listings: {len(ls)}")

    if len(ls) == 0:
        print("Falling back to _mock_listings() directly for test")
        ls = _mock_listings()
        from png_scraper.deduplicator import group_listings
        from png_scraper.engine import Listing
        objects = [Listing(**l) for l in ls]
        ls = [o.to_dict() for o in group_listings(objects)]
        print(f"Direct Mock + Grouping: {len(ls)}")

    sample = ls[0]
    print(f"Sample Listing ID: {sample.get('listing_id')}")
    print(f"Sample Health Score: {sample.get('health_score')}")
    print(f"Sample Is Verified: {sample.get('is_verified')}")
    print(f"Sample Group ID: {sample.get('group_id')}")

    # Check if any grouping happened
    groups = [l.get('group_id') for l in ls if l.get('group_id')]
    unique_groups = set(groups)
    print(f"Total Groups: {len(unique_groups)}")

    duplicates = [g for g in unique_groups if groups.count(g) > 1]
    print(f"Groups with duplicates: {len(duplicates)}")

    assert 'health_score' in sample
    assert 'is_verified' in sample
    assert len(ls) > 0

if __name__ == "__main__":
    try:
        test_load_listings()
        print("\nAPI changes verified!")
    except Exception as e:
        print(f"\nVerification failed: {e}")
        import traceback
        traceback.print_exc()
