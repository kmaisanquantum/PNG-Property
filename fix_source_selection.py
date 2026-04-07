import re

file_path = 'backend/png_scraper/main.py'
with open(file_path, 'r') as f:
    content = f.read()

pattern = r'def _want\(name: str\) -> bool:\n\s+return sources is None or name\.lower\(\) in \[s\.lower\(\) for s in sources\]'
replacement = '''def _want(name: str) -> bool:
        if sources is None: return True
        low_sources = [s.lower() for s in sources]
        if name.lower() in low_sources: return True

        # Category handling
        portals = ["hausples", "png real estate", "png buy n rent", "professionals"]
        if "portals" in low_sources and name.lower() in portals: return True
        if "agencies" in low_sources and name.lower() not in portals and name.lower() != "facebook": return True
        return False'''

new_content = re.sub(pattern, replacement, content)

with open(file_path, 'w') as f:
    f.write(new_content)
