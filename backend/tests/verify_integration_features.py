import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.notifier import detect_price_drops, match_saved_searches
from png_scraper.messenger_bot import InquiryBot, qualify_lead

def test_price_drops():
    print("Testing Price Drop Detection...")
    old = [{"listing_id": "L1", "price_monthly_k": 5000}]
    new = [{"listing_id": "L1", "title": "Test", "price_monthly_k": 4500, "listing_url": "http://test"}]
    drops = detect_price_drops(old, new)
    print(f"  Drops found: {len(drops)}")
    assert len(drops) == 1
    assert drops[0]["drop_pct"] == 10.0

def test_matching():
    print("Testing Saved Search Matching...")
    new = [
        {"listing_id": "L1", "suburb": "Waigani", "price_monthly_k": 2000, "property_type": "Apartment"},
        {"listing_id": "L2", "suburb": "Boroko", "price_monthly_k": 5000, "property_type": "House"}
    ]
    searches = [
        {"user_id": "U1", "name": "Cheap Waigani", "criteria": {"suburb": "Waigani", "max_price": 2500}}
    ]
    matches = match_saved_searches(new, searches)
    print(f"  Matches found: {len(matches)}")
    assert len(matches) == 1
    assert matches[0]["listing"]["listing_id"] == "L1"

def test_messenger_bot():
    print("Testing Messenger Bot Logic...")
    bot = InquiryBot("user123")
    q1 = bot.get_next_question()
    assert "budget" in q1.lower()

    bot.process_answer("K5000") # budget
    bot.process_answer("Waigani") # location
    bot.process_answer("Immediately") # timeline
    res = bot.process_answer("K10000") # income

    print(f"  Bot Final Response: {res}")
    assert bot.state == "COMPLETE"

    qualification = qualify_lead(bot.answers)
    print(f"  Lead Qualified: {qualification['is_qualified']} (Score: {qualification['score']})")
    assert qualification["is_qualified"] == True
    assert qualification["score"] >= 80

if __name__ == "__main__":
    try:
        test_price_drops()
        test_matching()
        test_messenger_bot()
        print("\n✅ Integration Features Logic Tests Passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
