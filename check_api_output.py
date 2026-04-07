import sys
import os
import json
from datetime import datetime, timezone

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import _market_score

def check_structure():
    price = 3500
    suburb = "Boroko"

    result = _market_score(price, suburb)
    print(json.dumps(result, indent=2))

    expected_keys = ["pct_vs_avg", "benchmark_avg", "investment_score", "investment_flags", "label", "color"]
    for key in expected_keys:
        if key not in result:
            print(f"FAILED: Missing key {key}")
            sys.exit(1)

    print("API Metadata Structure Check PASSED")

if __name__ == "__main__":
    check_structure()
