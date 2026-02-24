# PNG Property Dashboard — System Architecture

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES (10+)                          │
│  Hausples · The Professionals · Ray White · Century 21 · MarketMeri │
│  SRE PNG · DAC · AAA Properties · Arthur Strachan · Facebook Mkt    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  Playwright (stealth Chromium)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SCRAPER LAYER                                │
│  PNGScraper (ABC)                                                   │
│    ├── HausplesScraper       React SPA, lazy-load, multi-page       │
│    ├── ProfessionalsScraper  WordPress/RealHomes theme              │
│    ├── GeneralAgencyScraper  Adaptive generic selectors (8 sites)   │
│    └── FacebookScraper       Stealth + login + infinite scroll      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  raw listing dicts
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     NORMALISATION ENGINE                            │
│  normalise_price()   K500/week → 2167 PGK/month (confidence: high) │
│  detect_suburb()     "Tokerara" → "Tokarara" (alias map, 24 keys)  │
│  classify_type()     "3 bedroom flat" → "Apartment"                │
│  extract_bedrooms()  "3BR", "3 bed", "b/r: 3" → 3                  │
│  deduplicate()       URL hash + fuzzy (suburb+price+type+beds)      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  Listing dataclass
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ANALYTICS ENGINE                               │
│  score_market_value()   Deal / Fair / Overpriced vs suburb avg      │
│  flag_middleman()       price > 40% above benchmark                 │
│  compute_suburb_stats() avg, median, min, max, sample_size         │
│  compute_trends()       8-week price history per suburb             │
└─────────────┬─────────────────────────────────────┬────────────────┘
              │                                     │
              ▼                                     ▼
   ┌──────────────────┐                  ┌──────────────────┐
   │   MongoDB Atlas  │                  │  output/*.json   │
   │  png_realestate  │                  │  output/*.csv    │
   └────────┬─────────┘                  └──────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FASTAPI REST API                              │
│  GET  /api/listings            Paginated, filterable listings       │
│  GET  /api/analytics/overview  KPI summary                          │
│  GET  /api/analytics/heatmap   Per-suburb stats                     │
│  GET  /api/analytics/trends    Weekly price trends                  │
│  GET  /api/analytics/supply-demand                                  │
│  GET  /api/analytics/sources   By-source breakdown                  │
│  GET  /api/analytics/middleman-flags                                │
│  POST /api/scrape/trigger      Async background job                 │
│  GET  /api/scrape/status/{id}  Job progress polling                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     REACT DASHBOARD (5 Views)                       │
│  Dashboard  — KPIs, heatmap, trends, supply/demand, sources         │
│  Listings   — Filtered table, market scores, middleman flags        │
│  Heatmap    — SVG bubble map, suburb tiles, ranking sidebar         │
│  Analytics  — Deep dive charts and supply/demand cards              │
│  Flagged    — Overpriced report sorted by worst offenders           │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   LANDING PAGE (standalone HTML)                    │
│  Hero + live ticker + animated stat counters                        │
│  Feature showcase (locked vs unlocked preview)                      │
│  Suburb heatmap teaser (6 locked)                                   │
│  Testimonials + Pricing (Free / Pro K49 / Enterprise)               │
│  Full auth modal: Email / Phone OTP / WhatsApp / Google / FB / Apple│
└─────────────────────────────────────────────────────────────────────┘
```

## Suburb Geocoding Reference

| Suburb | Lat | Lng | Avg Rent (PGK/mo) |
|--------|-----|-----|-------------------|
| Gordons | -9.4201 | 147.1739 | 5,957 |
| Waigani | -9.4298 | 147.1812 | 4,470 |
| Badili | -9.4600 | 147.1900 | 3,325 |
| Boroko | -9.4453 | 147.1769 | 3,150 |
| Koki | -9.4721 | 147.1847 | 2,900 |
| Tokarara | -9.4580 | 147.1700 | 2,275 |
| Erima | -9.4400 | 147.1580 | 2,033 |
| Gerehu | -9.4736 | 147.1609 | 1,880 |
| Morata | -9.4680 | 147.1540 | 1,633 |
| Hohola | -9.4512 | 147.1651 | 1,600 |
| Six Mile | -9.4150 | 147.1500 | 1,450 |
| Eight Mile | -9.3900 | 147.1420 | 1,225 |

## Price Period Multipliers

| Input Period | Multiplier | Confidence |
|---|---|---|
| `/day`, `daily` | × 30 | high |
| `/week`, `weekly` | × 4.3333 | high |
| `fortnight`, `fn` | × 2.16665 | high |
| `/month`, `monthly` | × 1 | high |
| `/year`, `pa` | × 0.0833 | high |
| ≤ 2000, no period | × 4.3333 | medium (assumed weekly) |
| > 2000, no period | × 1 | medium (assumed monthly) |
| no number found | — | low |
