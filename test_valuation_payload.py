import sys, os, json
from datetime import datetime, timezone

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import ValuationRequest

def test_payload():
    # This matches the new frontend form keys
    data = {"suburb": "Waigani", "property_type": "House", "bedrooms": 3, "sqm": 200}
    try:
        req = ValuationRequest(**data)
        print("Payload valid for backend model")
    except Exception as e:
        print(f"Payload INVALID: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_payload()
