import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.valuation_engine import estimate_property_value
import json

with open('output/png_listings_latest.json', 'r') as f:
    listings = json.load(f)

print("Total listings:", len(listings))
print("Sale listings:", len([l for l in listings if l.get('is_for_sale')]))
print("Rent listings:", len([l for l in listings if not l.get('is_for_sale')]))

# Case from screenshot: Sale, Boroko, House, 3 beds, 23000 sqm
result = estimate_property_value(listings, "Boroko", "House", 3, 23000.0, True)
print("\nResult for Sale:")
print(json.dumps(result, indent=2))

# Try Rent
result_rent = estimate_property_value(listings, "Boroko", "House", 3, 23000.0, False)
print("\nResult for Rent:")
print(json.dumps(result_rent, indent=2))
