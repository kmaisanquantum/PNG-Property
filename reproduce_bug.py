import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.main import export_json
from png_scraper.engine import Listing

# Mock data: a list of dictionaries (as produced by _run_scrape in main.py)
mock_merged = [
    {
        "listing_id": "123",
        "source_site": "Test",
        "title": "Test Listing",
        "price_raw": "K1000",
        "price_monthly_k": 1000,
        "price_confidence": "high",
        "location": "Test Loc",
        "listing_url": "http://test.com",
        "is_verified": True
    }
]

output_path = Path("output/test_reproduce.json")
output_path.parent.mkdir(exist_ok=True)

print("Attempting to call export_json with dictionaries...")
try:
    export_json(mock_merged, output_path)
    print("SUCCESS: export_json handled dictionaries.")
except Exception as e:
    print(f"FAILED: {e}")
