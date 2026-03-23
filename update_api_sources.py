with open('backend/main.py', 'r') as f:
    content = f.read()

search_sources = """    return {"sources":["Hausples","The Professionals","Ray White PNG","Century 21 PNG",
                       "MarketMeri","SRE PNG","DAC Properties","AAA Properties",
                       "Arthur Strachan","Pacific Palms","Facebook Marketplace"]}"""

replace_sources = """    return {"sources":[
        "Hausples", "PNG Real Estate", "MarketMeri", "PNG Buy n Rent",
        "LJ Hooker", "Ray White PNG", "Strickland Real Estate", "The Professionals",
        "Century 21", "Budget Real Estate", "Arthur Strachan", "DAC Real Estate",
        "Kenmok Real Estate", "Pacific Palms", "Credit Corp", "Nambawan Super",
        "Edai Town", "Facebook Marketplace"
    ]}"""

content = content.replace(search_sources, replace_sources)

with open('backend/main.py', 'w') as f:
    f.write(content)
