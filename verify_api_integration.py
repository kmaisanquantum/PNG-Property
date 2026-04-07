import sys
import os
import datetime

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import _market_score

def test_integration():
    # Test Waigani listing (close to hub, should have investment score)
    # BENCHMARKS["Waigani"] = 4470
    price = 4000
    suburb = "Waigani"

    result = _market_score(price, suburb)
    print(f"Result for {suburb} at K{price}:")
    print(f"  Investment Score: {result.get('investment_score')}")
    print(f"  Investment Flags: {result.get('investment_flags')}")

    assert "investment_score" in result
    assert result["investment_score"] > 50 # Should be good due to price and proximity

    # Test old listing
    old_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=100)).isoformat()
    result_old = _market_score(price, suburb, first_seen_at=old_date)
    print(f"Result for old listing:")
    print(f"  Investment Score: {result_old.get('investment_score')}")
    print(f"  Investment Flags: {result_old.get('investment_flags')}")
    assert "High Negotiation" in result_old.get('investment_flags', [])

if __name__ == "__main__":
    try:
        test_integration()
        print("Integration verification PASSED")
    except Exception as e:
        print(f"Integration verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
