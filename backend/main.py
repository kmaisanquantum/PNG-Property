"""
backend/main.py  —  PNG Property Dashboard API
FastAPI backend serving scraper control, analytics, and listing data.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("api")

app = FastAPI(
    title="PNG Property Dashboard API",
    description="Real-time PNG real estate aggregator and analytics API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── scrape job state (in-memory; use Redis in production) ─────────────────────
scrape_jobs: dict[str, dict] = {}

# ── helpers: load listings from output file or seed mock data ─────────────────

OUTPUT_FILE = Path("output/png_listings_latest.json")

def _load_listings() -> list[dict]:
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return _mock_listings()

def _mock_listings() -> list[dict]:
    """Rich mock dataset for development when scraper hasn't run yet."""
    suburbs = ["Waigani","Boroko","Gerehu","Gordons","Hohola","Tokarara","Koki","Badili","Six Mile","Eight Mile","Morata","Erima"]
    sources = ["Hausples","The Professionals","Ray White PNG","Century 21 PNG","MarketMeri","Facebook Marketplace","SRE PNG","DAC Properties"]
    types   = ["House","Apartment","Townhouse","Studio","Room","Compound"]
    verified = {"Facebook Marketplace": False}

    listings = []
    now = datetime.now(timezone.utc)
    for i in range(240):
        suburb  = random.choice(suburbs)
        src     = random.choice(sources)
        ptype   = random.choice(types)
        beds    = random.choice([1,2,3,4,5]) if ptype not in ("Studio","Room") else 1
        # Price ranges by suburb tier
        tier = {"Gordons":1,"Waigani":1,"Badili":2,"Boroko":2,"Koki":2,
                "Tokarara":3,"Gerehu":3,"Hohola":3,"Morata":4,"Erima":4,
                "Six Mile":4,"Eight Mile":4}.get(suburb, 3)
        base = [6000,3500,2000,1200][tier-1]
        price = int(random.gauss(base, base * 0.18))
        price = max(800, price)

        scraped = now - timedelta(hours=random.randint(0, 72))
        listings.append({
            "listing_id":      str(uuid.uuid4())[:16],
            "source_site":     src,
            "title":           f"{beds} Bedroom {ptype} – {suburb}",
            "price_raw":       f"K{price:,}/month",
            "price_monthly_k": price,
            "price_confidence":"high",
            "location":        f"{suburb}, NCD",
            "suburb":          suburb,
            "listing_url":     f"https://example.com/listing/{i+1}",
            "is_verified":     verified.get(src, True),
            "property_type":   ptype,
            "bedrooms":        beds,
            "scraped_at":      scraped.isoformat(),
            "raw_text":        f"{beds} bedroom {ptype.lower()} in {suburb} for rent K{price}/month",
        })
    return listings


# ── suburb benchmark stats ─────────────────────────────────────────────────────

SUBURB_COORDS = {
    "Waigani":   {"lat":-9.4298,"lng":147.1812},
    "Boroko":    {"lat":-9.4453,"lng":147.1769},
    "Gerehu":    {"lat":-9.4736,"lng":147.1609},
    "Gordons":   {"lat":-9.4201,"lng":147.1739},
    "Hohola":    {"lat":-9.4512,"lng":147.1651},
    "Tokarara":  {"lat":-9.4580,"lng":147.1700},
    "Koki":      {"lat":-9.4721,"lng":147.1847},
    "Badili":    {"lat":-9.4600,"lng":147.1900},
    "Six Mile":  {"lat":-9.4150,"lng":147.1500},
    "Eight Mile":{"lat":-9.3900,"lng":147.1420},
    "Morata":    {"lat":-9.4680,"lng":147.1540},
    "Erima":     {"lat":-9.4400,"lng":147.1580},
}

def _compute_suburb_stats(listings: list[dict]) -> list[dict]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for l in listings:
        if l.get("suburb") and l.get("price_monthly_k"):
            grouped[l["suburb"]].append(l["price_monthly_k"])

    result = []
    for suburb, prices in grouped.items():
        if not prices:
            continue
        avg = int(sum(prices) / len(prices))
        srt = sorted(prices)
        n   = len(srt)
        med = srt[n//2] if n % 2 else (srt[n//2-1]+srt[n//2])//2
        coords = SUBURB_COORDS.get(suburb, {"lat": -9.44, "lng": 147.18})
        result.append({
            "suburb":      suburb,
            "avg_price":   avg,
            "median_price":med,
            "min_price":   min(prices),
            "max_price":   max(prices),
            "listings":    n,
            "lat":         coords["lat"],
            "lng":         coords["lng"],
        })
    return sorted(result, key=lambda x: -x["avg_price"])


def _compute_trends(listings: list[dict]) -> list[dict]:
    """Weekly average price trend for top 3 suburbs over last 8 weeks."""
    top_suburbs = ["Waigani","Boroko","Gerehu"]
    now = datetime.now(timezone.utc)
    weeks = []
    for w in range(7, -1, -1):
        week_start = now - timedelta(weeks=w+1)
        week_end   = now - timedelta(weeks=w)
        label = (now - timedelta(weeks=w)).strftime("%b %d")
        week_data = {"week": label}
        for sub in top_suburbs:
            sub_prices = [
                l["price_monthly_k"] for l in listings
                if l.get("suburb") == sub
                and l.get("price_monthly_k")
                and week_start <= datetime.fromisoformat(l["scraped_at"].replace("Z","+00:00")) <= week_end
            ]
            # Fallback: use all prices with small noise if no data in that window
            if not sub_prices:
                all_sub = [l["price_monthly_k"] for l in listings if l.get("suburb")==sub and l.get("price_monthly_k")]
                if all_sub:
                    base = int(sum(all_sub)/len(all_sub))
                    sub_prices = [int(base * random.uniform(0.92, 1.08))]
            week_data[sub] = int(sum(sub_prices)/len(sub_prices)) if sub_prices else None
        weeks.append(week_data)
    return weeks


def _market_score(price: int, suburb: str) -> dict:
    BENCHMARKS = {
        "Waigani":4470,"Boroko":3150,"Gerehu":1880,"Gordons":5957,
        "Hohola":1600,"Tokarara":2275,"Koki":2900,"Badili":3325,
        "Six Mile":1450,"Eight Mile":1225,"Morata":1633,"Erima":2033,
    }
    avg = BENCHMARKS.get(suburb, 2800)
    pct = ((price - avg) / avg) * 100
    if pct <= -15:
        label = "Deal"
        color = "#4ade80"
    elif pct >= 15:
        label = "Overpriced"
        color = "#f87171"
    else:
        label = "Fair"
        color = "#facc15"
    return {"label": label, "pct_vs_avg": round(pct, 1), "color": color, "benchmark_avg": avg}


# ── Pydantic models ────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    sources: List[str] = ["hausples","professionals","agencies"]
    max_pages: int = 3
    include_facebook: bool = False
    headless: bool = True


# ── background scrape task ─────────────────────────────────────────────────────

async def _run_scrape(job_id: str, req: ScrapeRequest):
    scrape_jobs[job_id].update({"status":"running","started_at":datetime.now(timezone.utc).isoformat(),"progress":0,"collected":0})
    try:
        # In production, call: from png_scraper.main import run_all; listings = await run_all(...)
        # For demo we simulate scraping stages
        sources = req.sources
        total   = len(sources) * req.max_pages
        collected = 0
        for i, source in enumerate(sources):
            for p in range(req.max_pages):
                await asyncio.sleep(0.8)   # simulate page scrape
                collected += random.randint(8, 22)
                progress = int(((i * req.max_pages + p + 1) / total) * 100)
                scrape_jobs[job_id].update({"progress": progress, "collected": collected,
                                             "current_source": source, "current_page": p+1})

        # In production: save to OUTPUT_FILE
        scrape_jobs[job_id].update({
            "status":      "complete",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "progress":    100,
            "collected":   collected,
        })
        log.info(f"Job {job_id} complete — {collected} listings")
    except Exception as e:
        scrape_jobs[job_id].update({"status":"error","error":str(e)})
        log.error(f"Job {job_id} failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"service":"PNG Property Dashboard API","version":"1.0.0","status":"ok"}


@app.get("/api/listings")
def get_listings(
    suburb:   Optional[str] = None,
    source:   Optional[str] = None,
    type:     Optional[str] = None,
    min_price:Optional[int] = None,
    max_price:Optional[int] = None,
    verified: Optional[bool]= None,
    middleman:Optional[bool]= None,
    sort:     str = "scraped_at",
    order:    str = "desc",
    page:     int = 1,
    limit:    int = 20,
):
    """Paginated, filterable listing endpoint."""
    listings = _load_listings()

    # Filters
    if suburb:   listings = [l for l in listings if (l.get("suburb") or "").lower() == suburb.lower()]
    if source:   listings = [l for l in listings if source.lower() in (l.get("source_site") or "").lower()]
    if type:     listings = [l for l in listings if (l.get("property_type") or "").lower() == type.lower()]
    if min_price is not None: listings = [l for l in listings if (l.get("price_monthly_k") or 0) >= min_price]
    if max_price is not None: listings = [l for l in listings if (l.get("price_monthly_k") or 0) <= max_price]
    if verified is not None:  listings = [l for l in listings if l.get("is_verified") == verified]

    # Inject market score
    for l in listings:
        if l.get("price_monthly_k") and l.get("suburb"):
            l["market_value"] = _market_score(l["price_monthly_k"], l["suburb"])

    # Sort
    reverse = (order == "desc")
    try:
        listings.sort(key=lambda x: x.get(sort) or "", reverse=reverse)
    except Exception:
        pass

    total  = len(listings)
    offset = (page - 1) * limit
    return {
        "total":    total,
        "page":     page,
        "pages":    max(1, (total + limit - 1) // limit),
        "limit":    limit,
        "listings": listings[offset:offset+limit],
    }


@app.get("/api/analytics/overview")
def get_overview():
    """KPI cards for dashboard header."""
    listings = _load_listings()
    priced   = [l for l in listings if l.get("price_monthly_k")]
    prices   = [l["price_monthly_k"] for l in priced]
    verified = [l for l in listings if l.get("is_verified")]

    # Middleman detection: price > 40% above suburb avg
    middlemen = 0
    for l in priced:
        score = _market_score(l["price_monthly_k"], l.get("suburb",""))
        if score["pct_vs_avg"] >= 40:
            middlemen += 1

    return {
        "total_listings":    len(listings),
        "verified_listings": len(verified),
        "avg_rent_pgk":      int(sum(prices)/len(prices)) if prices else 0,
        "median_rent_pgk":   sorted(prices)[len(prices)//2] if prices else 0,
        "middleman_flags":   middlemen,
        "sources_active":    len(set(l.get("source_site") for l in listings)),
        "suburbs_tracked":   len(set(l.get("suburb") for l in listings if l.get("suburb"))),
        "last_scraped":      max((l.get("scraped_at","") for l in listings), default="Never"),
    }


@app.get("/api/analytics/heatmap")
def get_heatmap():
    """Per-suburb price heatmap data."""
    return {"suburbs": _compute_suburb_stats(_load_listings())}


@app.get("/api/analytics/trends")
def get_trends():
    """Weekly price trends for top suburbs."""
    return {"trends": _compute_trends(_load_listings())}


@app.get("/api/analytics/supply-demand")
def get_supply_demand():
    """Supply (listing count) and demand proxy per suburb."""
    listings = _load_listings()
    grouped  = defaultdict(list)
    for l in listings:
        if l.get("suburb"):
            grouped[l["suburb"]].append(l)

    result = []
    for suburb, items in grouped.items():
        verified_count = sum(1 for l in items if l.get("is_verified"))
        fb_count       = sum(1 for l in items if not l.get("is_verified"))
        avg_price      = int(sum(l["price_monthly_k"] for l in items if l.get("price_monthly_k")) / max(1, len(items)))
        result.append({
            "suburb":          suburb,
            "supply":          len(items),
            "verified_supply": verified_count,
            "social_supply":   fb_count,
            "avg_price":       avg_price,
            "demand_score":    min(100, 40 + verified_count * 3 + random.randint(0,15)),
        })
    return {"data": sorted(result, key=lambda x: -x["supply"])}


@app.get("/api/analytics/sources")
def get_sources():
    """Listing count by source for the sources breakdown chart."""
    listings = _load_listings()
    counts: dict[str, int] = defaultdict(int)
    for l in listings:
        counts[l.get("source_site","Unknown")] += 1
    return {"sources": [{"name":k,"count":v} for k,v in sorted(counts.items(), key=lambda x:-x[1])]}


@app.get("/api/analytics/middleman-flags")
def get_middleman_flags(limit: int = 20):
    """Listings flagged as potential middleman markup (>40% above suburb avg)."""
    listings = _load_listings()
    flagged  = []
    for l in listings:
        if l.get("price_monthly_k") and l.get("suburb"):
            score = _market_score(l["price_monthly_k"], l["suburb"])
            if score["pct_vs_avg"] >= 40:
                l["market_value"] = score
                flagged.append(l)
    flagged.sort(key=lambda x: x["market_value"]["pct_vs_avg"], reverse=True)
    return {"flagged": flagged[:limit], "total_flagged": len(flagged)}


@app.post("/api/scrape/trigger")
async def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """Launch a background scrape job. Returns job_id to poll."""
    job_id = str(uuid.uuid4())[:8]
    scrape_jobs[job_id] = {
        "job_id":    job_id,
        "status":    "queued",
        "sources":   req.sources,
        "max_pages": req.max_pages,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "progress":  0,
        "collected": 0,
    }
    background_tasks.add_task(_run_scrape, job_id, req)
    return scrape_jobs[job_id]


@app.get("/api/scrape/status/{job_id}")
def get_scrape_status(job_id: str):
    """Poll a scrape job's progress."""
    job = scrape_jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return job


@app.get("/api/scrape/jobs")
def list_jobs():
    """List all recent scrape jobs."""
    jobs = sorted(scrape_jobs.values(), key=lambda x: x.get("queued_at",""), reverse=True)
    return {"jobs": jobs[:20]}


@app.get("/api/suburbs")
def get_suburbs():
    """List all known suburbs with coords."""
    return {"suburbs": [{"name":k,"lat":v["lat"],"lng":v["lng"]} for k,v in SUBURB_COORDS.items()]}


@app.get("/api/sources")
def get_source_list():
    return {"sources":["Hausples","The Professionals","Ray White PNG","Century 21 PNG",
                       "MarketMeri","SRE PNG","DAC Properties","AAA Properties",
                       "Arthur Strachan","Pacific Palms","Facebook Marketplace"]}
