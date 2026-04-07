import re

file_path = 'backend/main.py'
with open(file_path, 'r') as f:
    content = f.read()

pattern = r'def _market_score\(price:int,suburb:str\)->dict:.*?return\s+{"label":"Fair",.*?"benchmark_avg":avg}'
replacement = '''def _market_score(price:int, suburb:str, first_seen_at:str=None)->dict:
    avg = BENCHMARKS.get(suburb, 2800)
    pct = round(((price - avg) / avg) * 100, 1)

    # Compute investment score
    sub_coords = SUBURB_COORDS.get(suburb, {"lat": -9.44, "lng": 147.18})
    inv_score, inv_flags = calculate_investment_score(
        price,
        avg,
        sub_coords["lat"],
        sub_coords["lng"],
        first_seen_at or datetime.now(timezone.utc).isoformat()
    )

    result = {
        "pct_vs_avg": pct,
        "benchmark_avg": avg,
        "investment_score": inv_score,
        "investment_flags": inv_flags
    }

    if pct <= -15:
        result.update({"label": "Deal", "color": "#4ade80"})
    elif pct >= 15:
        result.update({"label": "Overpriced", "color": "#f87171"})
    else:
        result.update({"label": "Fair", "color": "#facc15"})

    return result'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(new_content)
