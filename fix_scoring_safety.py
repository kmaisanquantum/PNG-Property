import re

file_path = 'backend/main.py'
with open(file_path, 'r') as f:
    content = f.read()

pattern = r'# Compute investment score\n\s+sub_coords = SUBURB_COORDS\.get\(suburb, {"lat": -9\.44, "lng": 147\.18}\)\n\s+inv_score, inv_flags = calculate_investment_score\(\n\s+price, \n\s+avg, \n\s+sub_coords\["lat"\], \n\s+sub_coords\["lng"\],\n\s+first_seen_at or datetime\.now\(timezone\.utc\)\.isoformat\(\)\n\s+\)'
replacement = '''# Compute investment score
    try:
        sub_coords = SUBURB_COORDS.get(suburb, {"lat": -9.44, "lng": 147.18})
        inv_score, inv_flags = calculate_investment_score(
            price,
            avg,
            sub_coords["lat"],
            sub_coords["lng"],
            first_seen_at or datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        log.error(f"Investment scoring failed: {e}")
        inv_score, inv_flags = 0.0, []'''

new_content = re.sub(pattern, replacement, content)

with open(file_path, 'w') as f:
    f.write(new_content)
