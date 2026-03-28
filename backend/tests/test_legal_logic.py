import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.normalizer import classify_title_status, detect_legal_flags

def test_title_classification():
    print("Testing Title Classification...")

    t1 = "Beautiful 3br house with state lease title."
    s1 = classify_title_status(t1)
    print(f"  Input: {t1} -> {s1}")
    assert s1 == "State Lease"

    t2 = "ILG land available for sale, clan owned."
    s2 = classify_title_status(t2)
    print(f"  Input: {t2} -> {s2}")
    assert s2 == "Customary (ILG)"

    t3 = "Cheap room for rent."
    s3 = classify_title_status(t3)
    print(f"  Input: {t3} -> {s3}")
    assert s3 == "Unknown / TBC"

def test_legal_flags():
    print("Testing Legal Red Flags...")

    t1 = "Property under dispute, serious buyers only."
    f1 = detect_legal_flags(t1)
    print(f"  Input: {t1} -> {f1}")
    assert "Dispute" in f1

    t2 = "Title paperwork in progress, waiting for ILG."
    f2 = detect_legal_flags(t2)
    print(f"  Input: {t2} -> {f2}")
    assert "Unclear" in f2

    t3 = "Caveat registered on this section."
    f3 = detect_legal_flags(t3)
    print(f"  Input: {t3} -> {f3}")
    assert "Caveat" in f3

if __name__ == "__main__":
    try:
        test_title_classification()
        test_legal_flags()
        print("\n✅ Legal Classification Logic Verified!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
