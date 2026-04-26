"""
backend/main.py — PNG Property Intelligence Dashboard API
FastAPI backend for Render Web Service deployment.
"""
from __future__ import annotations
import asyncio, json, logging, os, random, uuid
from dotenv import load_dotenv
load_dotenv()
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from services.scoring_engine import calculate_investment_score
from jose import JWTError, jwt
import bcrypt
from png_scraper.serpapi_client import get_serpapi_places

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
log = logging.getLogger("api")

SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200 # 30 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password: str, hashed_password: str):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        log.error(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

app = FastAPI(
    title="PNG Property Intelligence Dashboard API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scrape_jobs: dict[str, dict] = {}
OUTPUT_FILE = Path(os.getenv("OUTPUT_FILE", "output/png_listings_latest.json"))
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "output/suburb_history.json"))
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path("static")

# ── MARKET CONTEXT DATA ───────────────────────────────────────────────────────
SUBURB_COORDS = {
    "Waigani":   {"lat": -9.4224, "lng": 147.1831},
    "Boroko":    {"lat": -9.4723, "lng": 147.2000},
    "Gerehu":    {"lat": -9.3891, "lng": 147.1633},
    "Gordons":   {"lat": -9.4477, "lng": 147.1944},
    "Hohola":    {"lat": -9.4609, "lng": 147.1831},
    "Tokarara":  {"lat": -9.4303, "lng": 147.1662},
    "Koki":      {"lat": -9.4801, "lng": 147.1704},
    "Badili":    {"lat": -9.4786, "lng": 147.1789},
    "Six Mile":  {"lat": -9.4613, "lng": 147.2146},
    "Eight Mile": {"lat": -9.4226, "lng": 147.2218},
    "Morata":    {"lat": -9.4086, "lng": 147.1887},
    "Erima":     {"lat": -9.4483, "lng": 147.1752},
    "Konedobu":   {"lat": -9.4750, "lng": 147.1550},
    "Edai Town":  {"lat": -9.3250, "lng": 147.1000},
    "Tuhava":     {"lat": -9.3800, "lng": 147.0500},
    "Kaugere":    {"lat": -9.4850, "lng": 147.1850},
    "Sabama":     {"lat": -9.4800, "lng": 147.1950},
    "Manu":       {"lat": -9.4750, "lng": 147.2050},
    "Vada Vada":  {"lat": -9.4650, "lng": 147.2000},
    "Taurama":    {"lat": -9.5100, "lng": 147.2200},
    "5 Mile":     {"lat": -9.4550, "lng": 147.2000},
    "Chinatown":  {"lat": -9.4450, "lng": 147.2100},
    "East Boroko":{"lat": -9.4750, "lng": 147.2100},
    "7 Mile":     {"lat": -9.4450, "lng": 147.2200},
    "9 Mile":     {"lat": -9.4100, "lng": 147.2300},
    "Bomana":     {"lat": -9.3700, "lng": 147.2400},
    "Laloki":     {"lat": -9.3400, "lng": 147.2500},
    "Goldie":     {"lat": -9.3000, "lng": 147.2700},
    "14 Mile":    {"lat": -9.4200, "lng": 147.3500},
    "Sogeri":     {"lat": -9.4200, "lng": 147.4200},
    "Rainbow":    {"lat": -9.4100, "lng": 147.1500},
    "Baruni":     {"lat": -9.4300, "lng": 147.1200},
    "Ensisi":     {"lat": -9.4150, "lng": 147.1700},
    "June Valley":{"lat": -9.4400, "lng": 147.1600},
}

BENCHMARKS = {
    "Waigani":4470,"Boroko":3150,"Gerehu":1880,"Gordons":5957,
    "Hohola":1600,"Tokarara":2275,"Koki":2900,"Badili":3325,
    "Six Mile":1450,"Eight Mile":1225,"Morata":1633,"Erima":2033,
    "Konedobu":3500,"Edai Town":1500,"Tuhava":1200,"Kaugere":1100,
    "Sabama":1100,"Manu":2200,"Vada Vada":1800,"Taurama":1400,
    "5 Mile":2800,"Chinatown":3200,"East Boroko":3800,"7 Mile":2100,
    "9 Mile":1600,"Bomana":1000,"Laloki":900,"Goldie":800,
    "14 Mile":1200,"Sogeri":1500,"Rainbow":2400,"Baruni":1100,
    "Ensisi":2600,"June Valley":1900,
}

# Suburb Pricing Tiers for Mock Data Generation
TIERS = {
    "Gordons":1,"Waigani":1,"Badili":2,"Boroko":2,"Koki":2,
    "Tokarara":3,"Gerehu":3,"Hohola":3,"Morata":4,"Erima":4,
    "Six Mile":4,"Eight Mile":4,
    "Konedobu":2,"Edai Town":4,"Tuhava":4,"Kaugere":4,
    "Sabama":4,"Manu":3,"Vada Vada":3,"Taurama":4,
    "5 Mile":2,"Chinatown":2,"East Boroko":2,"7 Mile":3,
    "9 Mile":4,"Bomana":4,"Laloki":4,"Goldie":4,
    "14 Mile":4,"Sogeri":4,"Rainbow":3,"Baruni":4,
    "Ensisi":3,"June Valley":3,
}
BASES = [6000, 3500, 2000, 1200]

def _get_db():
    mongo_url = os.getenv("MONGODB_URL","")
    if not mongo_url: return None
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=4000)
        return client["png_realestate"]
    except Exception as e:
        log.warning(f"MongoDB connection failed: {e}")
        return None

class User(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str = "buyer" # buyer, agent, lender, developer
    auth_provider: str = "email" # email, google, facebook, phone, whatsapp
    saved_searches: List[dict] = []
    notification_prefs: dict = {"whatsapp": True, "email": False}
    documents: List[dict] = []
    api_keys: List[dict] = []

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "buyer"
    auth_provider: str = "email"

class UserInDB(User):
    hashed_password: Optional[str] = None

users_db: dict[str, UserInDB] = {}
_listings_cache: dict = {"data": [], "timestamp": None}

def _load_listings() -> list[dict]:
    # Performance Optimization: Cache deduplicated listings based on file modification time
    mtime = OUTPUT_FILE.stat().st_mtime if OUTPUT_FILE.exists() else 0
    if _listings_cache["timestamp"] == mtime and _listings_cache["data"]:
        return _listings_cache["data"]

    raw_ls = []
    db = _get_db()
    if db is not None:
        try:
            raw_ls = list(db["listings"].find({},{"_id":0}).limit(2000))
        except Exception as e:
            log.warning(f"MongoDB query failed: {e}")

    if not raw_ls:
        if OUTPUT_FILE.exists():
            try:
                with open(OUTPUT_FILE) as f: raw_ls = json.load(f)
            except Exception as e:
                log.error(f"Failed to load {OUTPUT_FILE}: {e}")
                raw_ls = []
        else:
            raw_ls = []

    # Apply Deduplication & Grouping
    from png_scraper.engine import Listing
    from png_scraper.deduplicator import group_listings

    objects = []
    for d in raw_ls:
        try:
            obj = Listing(
                listing_id=d["listing_id"], source_site=d["source_site"], title=d["title"],
                price_raw=d["price_raw"], price_monthly_k=d.get("price_monthly_k"),
                price_confidence=d.get("price_confidence", "medium"), location=d["location"],
                suburb=d.get("suburb"), listing_url=d["listing_url"], is_verified=d.get("is_verified", False),
                property_type=d.get("property_type"), bedrooms=d.get("bedrooms"), sqm=d.get("sqm"),
                is_for_sale=d.get("is_for_sale", False), is_active=d.get("is_active", True),
                health_score=d.get("health_score", 0),
                is_middleman=d.get("is_middleman", False), group_id=d.get("group_id"),
                title_status=d.get("title_status", "Unknown / TBC"),
                legal_flags=d.get("legal_flags", []),
                scraped_at=d.get("scraped_at", ""), first_seen_at=d.get("first_seen_at", ""),
                raw_text=d.get("raw_text", "")
            )
            objects.append(obj)
        except Exception as e:
            log.error(f"Error hydrating listing {d.get('listing_id')}: {e}")

    grouped_objects = group_listings(objects)
    processed = [o.to_dict() for o in grouped_objects]

    # Update cache
    _listings_cache["data"] = processed
    _listings_cache["timestamp"] = mtime
    return processed

def get_user_by_identifier(identifier: str) -> Optional[UserInDB]:
    # Check in-memory first
    if identifier in users_db:
        return users_db[identifier]
    # Check MongoDB
    db = _get_db()
    if db is None: return None
    user_doc = db["users"].find_one({"$or": [{"email": identifier}, {"phone": identifier}]})
    if user_doc:
        return UserInDB(**user_doc)
    return None
def create_user(user: UserCreate) -> UserInDB:
    hashed_password = get_password_hash(user.password) if user.password else None
    # Filter out sensitive fields or those handled separately
    user_data = user.model_dump(exclude={"password"})
    user_in_db = UserInDB(
        **user_data,
        hashed_password=hashed_password,
        disabled=False
    )

    identifier = user.email or user.phone
    if not identifier:
        raise ValueError("User must have an email or phone number")

    # Save to MongoDB if available
    db = _get_db()
    if db is not None:
        try:
            query = {"$or": []}
            if user.email: query["$or"].append({"email": user.email})
            if user.phone: query["$or"].append({"phone": user.phone})
            db["users"].update_one(query, {"$set": user_in_db.model_dump()}, upsert=True)
        except Exception as e:
            log.warning(f"MongoDB save failed: {e}")

    # Always keep in memory for immediate access/reliability
    if user.email: users_db[user.email] = user_in_db
    if user.phone: users_db[user.phone] = user_in_db
    return user_in_db

@app.on_event("startup")
async def startup_event():
    # Ensure admin user exists
    admin_email = "kmaisan@dspng.tech"
    admin_pass = "kilomike@2024"
    try:
        log.info(f"Ensuring admin user: {admin_email}")
        create_user(UserCreate(email=admin_email, password=admin_pass, full_name="Admin User"))
    except Exception as e:
        log.error(f"Failed to seed admin user: {e}")

def _mock_listings() -> list[dict]:
    suburbs=["Waigani","Boroko","Gerehu","Gordons","Hohola","Tokarara","Koki","Badili","Six Mile","Eight Mile","Morata","Erima"]
    sources=["Hausples","The Professionals","Ray White PNG","Century 21 PNG","Marketmeri.com (Real Estate Section)","Facebook Marketplace","SRE PNG","DAC Properties"]
    types=["House","Apartment","Townhouse","Studio","Room","Compound"]
    no_verify={"Facebook Marketplace"}

    rng=random.Random(42); now=datetime.now(timezone.utc); listings=[]
    for i in range(240):
        suburb=rng.choice(suburbs); src=rng.choice(sources); ptype=rng.choice(types)
        is_sale = rng.random() < 0.2

        beds=rng.choice([1,2,3,4,5]) if ptype not in ("Studio","Room") else 1
        base=BASES[TIERS.get(suburb,3)-1]

        if is_sale:
            price = int(rng.gauss(base * 12 * 10, base * 12 * 2))
            price_raw = f"K{price:,}"
        else:
            price=max(800,int(rng.gauss(base,base*0.18)))
            price_raw = f"K{price:,}/month"

        scraped=now-timedelta(days=rng.randint(0,30), hours=rng.randint(0,24))
        first_seen = scraped - timedelta(days=rng.randint(0,14))
        sqm = rng.randint(40, 400) if ptype != "Room" else rng.randint(10, 25)

        is_verified = src not in no_verify
        # Randomly verify some FB listings via the new landline registry logic
        if src == "Facebook Marketplace" and rng.random() < 0.15:
            is_verified = True

        health = rng.randint(40, 95) if src == "Facebook Marketplace" else rng.randint(85, 100)

        t_status = rng.choice(["State Lease", "Customary (ILG)", "Unknown / TBC"])
        l_flags = []
        if t_status == "Unknown / TBC" and rng.random() < 0.3: l_flags = ["Dispute"]
        if t_status == "State Lease" and rng.random() < 0.05: l_flags = ["Caveat"]

        listings.append({"listing_id":f"lst{i:04d}","source_site":src,"title":f"{beds} Bedroom {ptype} – {suburb}",
            "price_raw":price_raw,"price_monthly_k":price,"price_confidence":"high",
            "location":f"{suburb}, NCD","suburb":suburb,"listing_url":f"https://hausples.com.pg/listing/{i+1}",
            "is_verified":is_verified,"property_type":ptype,"bedrooms":beds,
            "sqm": sqm, "is_for_sale": is_sale, "health_score": health,
            "is_middleman": rng.random() < 0.2, "group_id": None,
            "title_status": t_status, "legal_flags": l_flags,
            "scraped_at":scraped.isoformat(),"first_seen_at": first_seen.isoformat(),
            "raw_text":f"{beds} bedroom {ptype.lower()} in {suburb} {price_raw}"})
    return listings

def _market_score(price:int, suburb:str, first_seen_at:str=None)->dict:
    avg = BENCHMARKS.get(suburb, 2800)
    pct = round(((price - avg) / avg) * 100, 1)

    # Compute investment score
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
        inv_score, inv_flags = 0.0, []

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

    return result


def _suburb_stats(listings):
    # Separate rent and sale
    rent_grouped = defaultdict(list)
    sale_grouped = defaultdict(list)
    now = datetime.now(timezone.utc)

    for l in listings:
        sub = l.get("suburb")
        if not sub: continue

        if l.get("is_for_sale"):
            sale_grouped[sub].append(l)
        else:
            rent_grouped[sub].append(l)

    result = []
    for sub in set(list(rent_grouped.keys()) + list(sale_grouped.keys())):
        r_items = rent_grouped.get(sub, [])
        s_items = sale_grouped.get(sub, [])

        r_prices = [l["price_monthly_k"] for l in r_items if l.get("price_monthly_k")]
        s_prices = [l["price_monthly_k"] for l in s_items if l.get("price_monthly_k")] # This is total price for sale

        n_rent = len(r_prices)
        avg_rent = int(sum(r_prices)/n_rent) if n_rent else 0

        # Price per SQM (Separated)
        rent_sqm_list = [l["price_monthly_k"]/l["sqm"] for l in r_items if l.get("price_monthly_k") and l.get("sqm")]
        sale_sqm_list = [l["price_monthly_k"]/l["sqm"] for l in s_items if l.get("price_monthly_k") and l.get("sqm")]

        avg_rent_sqm = int(sum(rent_sqm_list)/len(rent_sqm_list)) if rent_sqm_list else 0
        avg_sale_sqm = int(sum(sale_sqm_list)/len(sale_sqm_list)) if sale_sqm_list else 0

        # Absorption Rate (Days on Market)
        # For active listings, DOM = (now - first_seen)
        # For inactive listings, DOM = (last_seen - first_seen)
        doms = []
        for l in (r_items + s_items):
            first = l.get("first_seen_at") or l.get("scraped_at")
            last = l.get("scraped_at")
            if first:
                try:
                    f_dt = datetime.fromisoformat(first.replace('Z', '+00:00'))
                    if l.get("is_active", True):
                        days = (now - f_dt).days
                    elif last:
                        l_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
                        days = (l_dt - f_dt).days
                    else:
                        days = (now - f_dt).days
                    doms.append(max(1, days))
                except: pass

        avg_dom = round(sum(doms)/len(doms), 1) if doms else 0

        # Rental Yield
        # Rule of thumb for PNG: Annual Rent / Sale Price
        # If no sale data, use benchmark sale prices derived from rent benchmarks (Cap Rate ~8-12%)
        avg_sale = int(sum(s_prices)/len(s_prices)) if s_prices else (BENCHMARKS.get(sub, 2500) * 12 * 10)
        yield_pct = round(((avg_rent * 12) / avg_sale) * 100, 2) if avg_sale > 0 else 0

        # Relative Performance Index
        # Example: "8-Mile sell 20% faster than 9-Mile"
        # We need a reference average DOM
        ref_avg_dom = 45 # Benchmark PNG average
        speed_index = round(((ref_avg_dom - avg_dom) / ref_avg_dom) * 100) if avg_dom > 0 else 0

        c = SUBURB_COORDS.get(sub, {"lat":-9.44, "lng":147.18})
        result.append({
            "suburb": sub,
            "avg_price": avg_rent,
            "median_price": int(sorted(r_prices)[n_rent//2]) if n_rent else 0,
            "min_price": min(r_prices) if n_rent else 0,
            "max_price": max(r_prices) if n_rent else 0,
            "avg_price_sqm": avg_sale_sqm or (avg_rent_sqm * 100), # Fallback: Cap Rate based estimate for heatmap
            "avg_rent_sqm": avg_rent_sqm,
            "avg_sale_sqm": avg_sale_sqm,
            "rental_yield": yield_pct,
            "absorption_rate": avg_dom, # average days on market
            "speed_index_pct": speed_index, # X% faster than average
            "listings": n_rent + len(s_items),
            "rent_count": n_rent,
            "sale_count": len(s_items),
            "lat": c["lat"], "lng": c["lng"]
        })

    return sorted(result, key=lambda x: -x["avg_price"])

def _trends(listings):
    top = ["Waigani", "Boroko", "Gerehu"]
    now = datetime.now(timezone.utc)

    # Try to load real history first
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                history = json.load(f)

            if len(history) >= 2:
                rows = []
                for entry in history:
                    row = {"week": datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00')).strftime("%b %d")}
                    sub_data = entry.get("suburbs", {})
                    for sub in top:
                        row[sub] = sub_data.get(sub, {}).get("avg_price", BENCHMARKS.get(sub, 2500))
                    rows.append(row)
                return rows
        except Exception as e:
            log.warning(f"Failed to use history for trends: {e}")

    # Fallback to simulated trends if history is too sparse
    rng = random.Random(99); rows = []
    for w in range(7, -1, -1):
        row = {"week": (now - timedelta(weeks=w)).strftime("%b %d")}
        for sub in top:
            all_p = [l["price_monthly_k"] for l in listings if l.get("suburb") == sub and l.get("price_monthly_k")]
            row[sub] = int((sum(all_p) / len(all_p)) * rng.uniform(0.93, 1.07)) if all_p else BENCHMARKS.get(sub, 2500)
        rows.append(row)
    return rows

class ScrapeRequest(BaseModel):
    sources: List[str] = ["hausples","professionals","agencies"]
    max_pages: int = 3
    include_facebook: bool = False
    headless: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None

def check_role(role: str):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role != role and user.role != "admin":
            raise HTTPException(status_code=403, detail="Operation not permitted for your role")
        return user
    return role_checker

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(sub=sub)
    except JWTError:
        raise credentials_exception
    user = get_user_by_identifier(token_data.sub)
    if user is None:
        raise credentials_exception
    return user

async def _run_scrape(job_id:str, req:ScrapeRequest):
    from png_scraper.main import run_all, export_json
    from png_scraper.notifier import detect_price_drops, match_saved_searches, notify_price_drop, notify_new_match

    # Load old listings for persistence and trend analysis
    old_listings = []
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE) as f: old_listings = json.load(f)
        except: pass

    old_map = {l["listing_id"]: l for l in old_listings}

    scrape_jobs[job_id].update({
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "progress": 5,
        "collected": 0,
        "current_source": "Initializing"
    })

    def on_progress(source_name, count, progress_pct):
        if job_id in scrape_jobs:
            current_total = scrape_jobs[job_id].get("collected", 0)
            scrape_jobs[job_id].update({
                "collected": current_total + count,
                "progress": round(5 + (progress_pct * 0.9)),
                "current_source": source_name
            })

    try:
        include_fb = req.include_facebook or any(s.lower() == "facebook" for s in req.sources)

        new_results = await run_all(
            include_facebook=include_fb,
            headless=req.headless,
            sources=req.sources,
            max_pages=req.max_pages,
            on_progress=on_progress
        )

        if new_results:
            now_str = datetime.now(timezone.utc).isoformat()
            merged = []
            seen_in_this_run = set()

            # Update or Add new listings
            for l_obj in new_results:
                l = l_obj.to_dict()
                lid = l["listing_id"]
                seen_in_this_run.add(lid)

                if lid in old_map:
                    # Persistence: Preserve the first time we ever saw this listing
                    l["first_seen_at"] = old_map[lid].get("first_seen_at") or old_map[lid].get("scraped_at")
                    l["scraped_at"] = now_str # Current "last seen"
                    l["is_active"] = True
                else:
                    l["first_seen_at"] = now_str
                    l["scraped_at"] = now_str
                    l["is_active"] = True
                merged.append(l)

            # Keep old listings that weren't in this scrape but mark as potentially inactive
            # Note: We only mark as inactive if they are older than 3 days without being seen
            for lid, old_l in old_map.items():
                if lid not in seen_in_this_run:
                    last_seen = old_l.get("scraped_at")
                    if last_seen:
                        dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        if (datetime.now(timezone.utc) - dt).days > 3:
                            old_l["is_active"] = False
                    merged.append(old_l)

            export_json(merged, OUTPUT_FILE)
            log.info(f"Scrape job {job_id} merged {len(merged)} listings (New: {len(new_results)}).")

            # --- HISTORICAL SNAPSHOT ---
            try:
                stats = _suburb_stats(merged)
                snapshot = {
                    "timestamp": now_str,
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "suburbs": {s["suburb"]: {"avg_price": s["avg_price"], "yield": s["rental_yield"]} for s in stats}
                }
                history = []
                if HISTORY_FILE.exists():
                    try:
                        with open(HISTORY_FILE) as f: history = json.load(f)
                    except: pass

                # Deduplicate by date (one snapshot per day max)
                today_str = snapshot["date"]
                history = [h for h in history if h.get("date") != today_str]
                history.append(snapshot)

                # Keep last 12 snapshots (roughly 3 months of weekly or 12 days of daily)
                history = history[-12:]
                with open(HISTORY_FILE, "w") as f: json.dump(history, f, indent=2)
            except Exception as e:
                log.error(f"Failed to save historical snapshot: {e}")

            # --- NOTIFICATIONS ---
            drops = detect_price_drops(old_listings, [r.to_dict() for r in new_results])
            for drop in drops:
                admin_phone = "+675 7000 0000"
                notify_price_drop(admin_phone, drop)

            all_saved = []
            for u in users_db.values():
                for s in u.saved_searches:
                    all_saved.append({"user_id": u.email or u.phone, "phone": u.phone, "name": s["name"], "criteria": s["criteria"]})

            matches = match_saved_searches([r.to_dict() for r in new_results], all_saved)
            for match in matches:
                if match["phone"]:
                    notify_new_match(match["phone"], match["search_name"], match["listing"])

        else:
            log.warning(f"Scrape job {job_id} collected 0 listings.")

        scrape_jobs[job_id].update({
            "status": "complete",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "progress": 100,
            "collected": len(new_results) if new_results else 0,
            "current_source": "Finished"
        })
    except Exception as e:
        log.error(f"Scrape job {job_id} failed: {e}")
        scrape_jobs[job_id].update({"status":"error","error":str(e)})

# ── Routes ────────────────────────────────────────────────────────────────────

@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def root_redirect():
    # Serve index.html if it exists, else redirect to docs
    if (STATIC_DIR / "index.html").is_file():
        return FileResponse(str(STATIC_DIR / "index.html"))
    return RedirectResponse(url="/api/docs")

@app.get("/api/health")
@app.get("/api")
@app.get("/api/")
def health(): return {"service":"PNG Property Intelligence Dashboard API","version":"1.0.0","status":"ok"}

@app.get("/api/config/status")
def get_config_status():
    fb_email = os.getenv("FB_EMAIL", "")
    fb_password = os.getenv("FB_PASSWORD", "")
    return {
        "facebook_configured": bool(fb_email and fb_password),
        "mongodb_configured": bool(os.getenv("MONGODB_URL", "")),
    }

@app.post("/api/auth/signup", response_model=User)
def signup(user: UserCreate):
    identifier = user.email or user.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Identifier (email or phone) is required")

    existing_user = get_user_by_identifier(user.email) if user.email else users_db.get(user.phone)
    if existing_user:
        raise HTTPException(status_code=400, detail="Identifier already registered")

    return create_user(user)

@app.get("/api/auth/check-identifier")
def check_identifier(q: str):
    """Seamless auth: Check if an email or phone already exists."""
    user = get_user_by_identifier(q)
    return {"exists": user is not None, "identifier": q, "provider": user.auth_provider if user else None}

@app.post("/api/auth/otp", response_model=Token)
async def otp_auth(provider: str, identifier: str, name: Optional[str] = None):
    """OTP Auth (Phone/WhatsApp). WARNING: For production, verify with provider SDK/API."""
    log.warning(f"OTP auth used for {identifier} via {provider}.")
    user = get_user_by_identifier(identifier)
    if not user:
        if not name:
            raise HTTPException(status_code=400, detail="Name is required for new users")
        # Create new user for otp if not exists
        user_create = UserCreate(
            email=identifier if "@" in identifier else None,
            phone=identifier if "@" not in identifier else None,
            full_name=name,
            auth_provider=provider
        )
        user = create_user(user_create)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": identifier}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user.email, "full_name": user.full_name, "phone": user.phone, "role": user.role}
    }

@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_identifier(form_data.username)
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email or user.phone}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@app.get("/api/listings")
def get_listings(suburb:Optional[str]=None,source:Optional[str]=None,type:Optional[str]=None,
    min_price:Optional[int]=None,max_price:Optional[int]=None,verified:Optional[bool]=None,
    title_status:Optional[str]=None, legal_flags:Optional[str]=None,
    sort:str="scraped_at",order:str="desc",page:int=1,limit:int=25,
    current_user: User = Depends(get_current_user)):
    ls=_load_listings()
    if suburb: ls=[l for l in ls if (l.get("suburb") or "").lower()==suburb.lower()]
    if source: ls=[l for l in ls if source.lower() in (l.get("source_site") or "").lower()]
    if type:   ls=[l for l in ls if (l.get("property_type") or "").lower()==type.lower()]
    if min_price: ls=[l for l in ls if (l.get("price_monthly_k") or 0)>=min_price]
    if max_price: ls=[l for l in ls if (l.get("price_monthly_k") or 0)<=max_price]
    if verified is not None: ls=[l for l in ls if l.get("is_verified")==verified]
    if title_status: ls=[l for l in ls if title_status.lower() in (l.get("title_status") or "").lower()]
    if legal_flags: ls=[l for l in ls if any(legal_flags.lower() in f.lower() for f in (l.get("legal_flags") or []))]

    for l in ls:
        if l.get("price_monthly_k") and l.get("suburb"): l["market_value"]=_market_score(l["price_monthly_k"],l["suburb"],l.get("first_seen_at"))
    try: ls.sort(key=lambda x:x.get(sort) or "",reverse=(order=="desc"))
    except: pass
    total=len(ls); offset=(page-1)*limit
    return {"total":total,"page":page,"pages":max(1,(total+limit-1)//limit),"limit":limit,"listings":ls[offset:offset+limit]}

@app.get("/api/analytics/overview")
def get_overview(current_user: User = Depends(get_current_user)):
    ls=_load_listings(); prices=[l["price_monthly_k"] for l in ls if l.get("price_monthly_k")]
    flags=sum(1 for l in ls if l.get("price_monthly_k") and l.get("suburb") and _market_score(l["price_monthly_k"],l["suburb"],l.get("first_seen_at"))["pct_vs_avg"]>=40)
    return {"total_listings":len(ls),"verified_listings":sum(1 for l in ls if l.get("is_verified")),
        "avg_rent_pgk":int(sum(prices)/len(prices)) if prices else 0,
        "median_rent_pgk":sorted(prices)[len(prices)//2] if prices else 0,"middleman_flags":flags,
        "sources_active":len(set(l.get("source_site") for l in ls)),
        "suburbs_tracked":len(set(l.get("suburb") for l in ls if l.get("suburb"))),
        "last_scraped":max((l.get("scraped_at","") for l in ls),default="Never")}

@app.get("/api/analytics/heatmap")
def get_heatmap(current_user: User = Depends(get_current_user)): return {"suburbs":_suburb_stats(_load_listings())}

@app.get("/api/analytics/trends")
def get_trends(current_user: User = Depends(get_current_user)): return {"trends":_trends(_load_listings())}

@app.get("/api/analytics/supply-demand")
def get_supply_demand(current_user: User = Depends(get_current_user)):
    grouped=defaultdict(list); rng=random.Random(7)
    for l in _load_listings():
        if l.get("suburb"): grouped[l["suburb"]].append(l)
    result=[]
    for suburb,items in grouped.items():
        prices=[l["price_monthly_k"] for l in items if l.get("price_monthly_k")]
        result.append({"suburb":suburb,"supply":len(items),
            "verified_supply":sum(1 for l in items if l.get("is_verified")),
            "unverified_supply":sum(1 for l in items if not l.get("is_verified")),
            "avg_price":int(sum(prices)/len(prices)) if prices else 0,
            "demand_score":min(100,40+sum(1 for l in items if l.get("is_verified"))*3+rng.randint(0,15))})
    return {"data":sorted(result,key=lambda x:-x["supply"])}

@app.get("/api/analytics/sources")
def get_sources_analytics(current_user: User = Depends(get_current_user)):
    counts=defaultdict(int)
    for l in _load_listings(): counts[l.get("source_site","Unknown")]+=1
    return {"sources":[{"name":k,"count":v} for k,v in sorted(counts.items(),key=lambda x:-x[1])]}

@app.get("/api/analytics/middleman-flags")
def get_middleman_flags(limit:int=20, current_user: User = Depends(get_current_user)):
    flagged=[]
    for l in _load_listings():
        if l.get("price_monthly_k") and l.get("suburb"):
            s=_market_score(l["price_monthly_k"],l["suburb"],l.get("first_seen_at"))
            if s["pct_vs_avg"]>=40: flagged.append({**l,"market_value":s})
    flagged.sort(key=lambda x:x["market_value"]["pct_vs_avg"],reverse=True)
    return {"flagged":flagged[:limit],"total_flagged":len(flagged)}

@app.post("/api/scrape/trigger")
async def trigger_scrape(req:ScrapeRequest,background_tasks:BackgroundTasks,current_user: User = Depends(get_current_user)):
    job_id=str(uuid.uuid4())[:8]
    scrape_jobs[job_id]={"job_id":job_id,"status":"queued","sources":req.sources,
        "max_pages":req.max_pages,"queued_at":datetime.now(timezone.utc).isoformat(),"progress":0,"collected":0}
    background_tasks.add_task(_run_scrape,job_id,req)
    return scrape_jobs[job_id]

@app.get("/api/scrape/status/{job_id}")
def get_scrape_status(job_id:str, current_user: User = Depends(get_current_user)):
    job=scrape_jobs.get(job_id)
    if not job: raise HTTPException(404,f"Job '{job_id}' not found")
    return job

@app.post("/api/scrape/clear")
def clear_scrape_data(current_user: User = Depends(get_current_user)):
    """Clears all listing and history data files to allow for a clean scrape."""
    try:
        if OUTPUT_FILE.exists(): OUTPUT_FILE.unlink()
        if HISTORY_FILE.exists(): HISTORY_FILE.unlink()
        _listings_cache["timestamp"] = 0
        _listings_cache["data"] = []
        # Also clear MongoDB if connected
        db = _get_db()
        if db is not None:
            db["listings"].delete_many({})
        return {"status": "ok", "message": "Data cleared successfully"}
    except Exception as e:
        raise HTTPException(500, f"Failed to clear data: {e}")

@app.get("/api/scrape/jobs")
def list_jobs(current_user: User = Depends(get_current_user)): return {"jobs":sorted(scrape_jobs.values(),key=lambda x:x.get("queued_at",""),reverse=True)[:20]}

@app.get("/api/suburbs")
def get_suburbs(current_user: User = Depends(get_current_user)): return {"suburbs":[{"name":k,"lat":v["lat"],"lng":v["lng"]} for k,v in SUBURB_COORDS.items()]}

@app.post("/api/developer/keys")
def generate_api_key(current_user: User = Depends(check_role("developer"))):
    new_key = {
        "key": f"png_{uuid.uuid4().hex[:16]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "usage_count": 0,
        "last_used": None
    }
    identifier = current_user.email or current_user.phone
    if identifier not in users_db:
        users_db[identifier] = UserInDB(**current_user.model_dump(), hashed_password=None)

    users_db[identifier].api_keys.append(new_key)

    db = _get_db()
    if db is not None:
        try:
            db["users"].update_one(
                {"$or": [{"email": current_user.email}, {"phone": current_user.phone}]},
                {"$push": {"api_keys": new_key}}
            )
        except: pass
    return new_key

@app.get("/api/developer/keys")
def get_api_keys(current_user: User = Depends(check_role("developer"))):
    return {"api_keys": current_user.api_keys}

@app.get("/api/v1/listings/export")
def developer_listing_export(api_key: str):
    """Simulated paid API endpoint for developers."""
    # 1. Check in-memory cache first
    found_user = None
    for u in users_db.values():
        if any(k["key"] == api_key for k in u.api_keys):
            found_user = u
            break

    # 2. Check Database if not found in memory
    if not found_user:
        db = _get_db()
        if db is not None:
            user_doc = db["users"].find_one({"api_keys.key": api_key})
            if user_doc:
                found_user = UserInDB(**user_doc)
                # Cache it for next time
                if found_user.email: users_db[found_user.email] = found_user
                if found_user.phone: users_db[found_user.phone] = found_user

    if not found_user:
        raise HTTPException(401, "Invalid API Key. Please get one from the Developer Portal.")

    # Increment usage (Mock)
    listings = _load_listings()
    return {
        "status": "success",
        "total": len(listings),
        "data": listings[:100] # Return first 100 for dev preview
    }

@app.get("/api/sources")
def get_source_list(current_user: User = Depends(get_current_user)):
    return {"sources":[
        "Hausples", "PNG Real Estate", "Marketmeri.com (Real Estate Section)", "PNG Buy n Rent",
        "LJ Hookers", "Ray White PNG", "Strickland Real Estate", "The Professionals",
        "Century 21 Siule Real Estate", "Budget Real Estate", "Arthur Strachan", "DAC Real Estate",
        "Kenmok Real Estate", "Pacific Palms Property", "Credit Corporation Properties", "Nambawan Super (Property)", "AAA Properties",
        "Edai Town Estate", "Tuhava", "Facebook Marketplace"
    ]}

# ── Notifications & Saved Searches ───────────────────────────────────────────

class FollowSearchRequest(BaseModel):
    name: str
    criteria: dict

@app.post("/api/notifications/follow")
def follow_search(req: FollowSearchRequest, current_user: User = Depends(get_current_user)):
    identifier = current_user.email or current_user.phone
    if identifier not in users_db:
        # For simplicity in this sandbox, we create the user in the mock DB if missing
        users_db[identifier] = UserInDB(**current_user.dict(), hashed_password=None)

    users_db[identifier].saved_searches.append({
        "name": req.name,
        "criteria": req.criteria,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    db = _get_db()
    if db is not None:
        try:
            db["users"].update_one(
                {"$or": [{"email": current_user.email}, {"phone": current_user.phone}]},
                {"$push": {"saved_searches": users_db[identifier].saved_searches[-1]}}
            )
        except: pass

    return {"status": "ok", "saved_searches_count": len(users_db[identifier].saved_searches)}

@app.get("/api/notifications/active")
def get_followed_searches(current_user: User = Depends(get_current_user)):
    user = get_user_by_identifier(current_user.email or current_user.phone)
    return {"saved_searches": user.saved_searches if user else []}

# ── Legal Guard & Title Search ──────────────────────────────────────────────

@app.get("/api/legal/title-search")
def title_search(listing_id: str, current_user: User = Depends(get_current_user)):
    """Simulates a land registry title search for a specific property."""
    listings = _load_listings()
    l = next((x for x in listings if x["listing_id"] == listing_id), None)
    if not l: raise HTTPException(404, "Listing not found")

    # Simulate a detailed registry lookup
    rng = random.Random(listing_id)
    status = l.get("title_status", "Unknown / TBC")
    flags = l.get("legal_flags", [])

    # If the listing says state lease, 80% chance it's verified in registry
    # If customary, 90% chance it has an associated ILG file
    is_verified = False
    if status == "State Lease": is_verified = rng.random() > 0.2
    elif status == "Customary (ILG)": is_verified = rng.random() > 0.1

    return {
        "listing_id": listing_id,
        "title_status": status,
        "registry_verified": is_verified,
        "last_searched": datetime.now(timezone.utc).isoformat(),
        "dispute_index": "Low" if not flags else "High",
        "legal_recommendation": "Safe to proceed" if is_verified and not flags else "Legal advisory recommended",
        "ilg_number": f"ILG-{rng.randint(1000,9999)}" if status == "Customary (ILG)" else None
    }

# ── Bank-Ready Document Vault ───────────────────────────────────────────────

ALLOWED_DOC_TYPES = {"ID", "Slip", "Nasfund", "Nambawan", "Offer"}
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5MB

@app.post("/api/vault/upload")
async def upload_vault_document(
    doc_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(400, f"Invalid document type. Allowed types: {ALLOWED_DOC_TYPES}")

    # Extension validation
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file extension. Allowed: {ALLOWED_EXTENSIONS}")

    # Size validation (rough check)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE/1024/1024}MB")
    await file.seek(0) # Reset pointer for writing

    identifier = current_user.email or current_user.phone
    user = get_user_by_identifier(identifier)
    if not user: raise HTTPException(404, "User not found")

    # Secure filename
    file_id = str(uuid.uuid4())[:8]
    ext = file.filename.split(".")[-1] if "." in file.filename else "dat"
    filename = f"{identifier.replace('@','_')}_{doc_type}_{file_id}.{ext}"
    file_path = UPLOAD_DIR / filename

    # In a real app, use S3 or a secure volume. Here we write to local disk.
    with open(file_path, "wb") as f:
        f.write(await file.read())

    doc_entry = {
        "id": file_id,
        "type": doc_type,
        "filename": file.filename,
        "path": str(file_path),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "Verified" # In reality, might be "Pending Review"
    }

    # Update user record
    # Find existing of same type and update or append
    existing = next((d for d in user.documents if d["type"] == doc_type), None)
    if existing:
        user.documents.remove(existing)
    user.documents.append(doc_entry)

    db = _get_db()
    if db is not None:
        try:
            db["users"].update_one(
                {"$or": [{"email": current_user.email}, {"phone": current_user.phone}]},
                {"$set": {"documents": user.documents}}
            )
        except: pass

    # Update in-memory
    if current_user.email: users_db[current_user.email] = user
    if current_user.phone: users_db[current_user.phone] = user

    return {"status": "ok", "document": doc_entry}

@app.get("/api/vault/status")
def get_vault_status(current_user: User = Depends(get_current_user)):
    user = get_user_by_identifier(current_user.email or current_user.phone)
    return {"documents": user.documents if user else []}

@app.post("/api/vault/package")
def package_vault(current_user: User = Depends(get_current_user)):
    """Simulates creating a shared digital folder for a bank lending officer."""
    user = get_user_by_identifier(current_user.email or current_user.phone)
    if not user or not user.documents:
        raise HTTPException(400, "No documents to package")

    share_token = str(uuid.uuid4())[:12]
    # In production, this would create a signed temporary link or a ZIP archive
    return {
        "status": "ready",
        "share_url": f"https://png-property.tech/share/vault/{share_token}",
        "document_count": len(user.documents),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }

# ── Integrated Property Valuation Engine (AVM) ───────────────────────────────

class ValuationRequest(BaseModel):
    suburb: str
    property_type: str
    bedrooms: int
    sqm: Optional[float] = None
    is_for_sale: bool = True

class UtilityReview(BaseModel):
    suburb: str
    street: Optional[str] = None
    utility: str # "power" or "water"
    rating: int # 1-5
    comment: Optional[str] = None

@app.post("/api/valuation/estimate")
def get_valuation_estimate(req: ValuationRequest, current_user: User = Depends(get_current_user)):
    from png_scraper.valuation_engine import estimate_property_value
    listings = _load_listings()
    estimate = estimate_property_value(
        listings, req.suburb, req.property_type, req.bedrooms, req.sqm, req.is_for_sale
    )
    if "error" in estimate:
        raise HTTPException(400, estimate["error"])
    return estimate

@app.post("/api/valuation/report")
def get_detailed_report(req: ValuationRequest, payment_ref: str, current_user: User = Depends(get_current_user)):
    """Unlocks a detailed PDF-style report after payment verification (mocked)."""
    # Mock Payment Verification (Lumi/Cellmoni)
    if not payment_ref.startswith("PAY-"):
        raise HTTPException(402, "Invalid or missing payment reference from Lumi/Cellmoni")

    from png_scraper.valuation_engine import estimate_property_value, generate_market_report
    listings = _load_listings()
    val = estimate_property_value(listings, req.suburb, req.property_type, req.bedrooms, req.sqm, req.is_for_sale)
    if "error" in val:
        raise HTTPException(400, val["error"])

    report = generate_market_report(val)
    report["payment_verified"] = True
    report["payment_ref"] = payment_ref
    return report

# ── Utility & Serviceability Map Layers ───────────────────────────────────────

# Static Data: Top Reputable Schools in Port Moresby
SCHOOLS = [
    {"name": "Korobosea International", "lat": -9.4750, "lng": 147.1820, "type": "International"},
    {"name": "Port Moresby International", "lat": -9.4580, "lng": 147.1950, "type": "International"},
    {"name": "Ela Murray International", "lat": -9.4780, "lng": 147.1680, "type": "International"},
    {"name": "St Joseph's International", "lat": -9.4520, "lng": 147.1740, "type": "International"},
    {"name": "Gordon International", "lat": -9.4250, "lng": 147.1850, "type": "International"},
]

# Static Data: Internet Coverage Zones (Mocked based on common high-speed areas)
INTERNET_ZONES = {
    "Waigani": {"fibre": True, "5g": True},
    "Boroko": {"fibre": True, "5g": True},
    "Gordons": {"fibre": True, "5g": True},
    "Town": {"fibre": True, "5g": True},
    "Gerehu": {"fibre": False, "5g": True},
    "Tokarara": {"fibre": False, "5g": False},
}

# Static Data: Planned Infrastructure Projects (Zoning Overlays)
INFRASTRUCTURE_PROJECTS = [
    {"name": "Duran Farm Housing Project", "lat": -9.3800, "lng": 147.1500, "type": "Residential Development"},
    {"name": "Eda Town Development", "lat": -9.4100, "lng": 147.1000, "type": "Mixed Use"},
    {"name": "Gerehu to 9-Mile Road Upgrade", "lat": -9.4000, "lng": 147.1600, "type": "Infrastructure"},
]

# In-memory crowdsourced utility reviews
utility_reviews: List[dict] = []
# Cache for SerpApi places to avoid redundant calls
serpapi_cache: dict[str, dict] = {}

@app.get("/api/heatmap/places")
def get_heatmap_places(category: str = "schools", current_user: User = Depends(get_current_user)):
    """Fetches POIs from SerpApi with a 24-hour cache."""
    now = datetime.now(timezone.utc)
    if category in serpapi_cache:
        cached_at = serpapi_cache[category]["timestamp"]
        if now - cached_at < timedelta(hours=24):
            return {"category": category, "places": serpapi_cache[category]["data"], "cached": True}

    places = get_serpapi_places(category)
    if places:
        serpapi_cache[category] = {"timestamp": now, "data": places}
        return {"category": category, "places": places, "cached": False}

    # Fallback to empty list or previously cached data if available
    return {"category": category, "places": serpapi_cache.get(category, {}).get("data", []), "cached": True}

@app.post("/api/utilities/review")
def add_utility_review(review: UtilityReview, current_user: User = Depends(get_current_user)):
    data = review.model_dump()
    data["user_id"] = current_user.email or current_user.phone
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    utility_reviews.append(data)
    return {"status": "ok", "total_reviews": len(utility_reviews)}

@app.get("/api/utilities/map")
def get_utility_map_data(current_user: User = Depends(get_current_user)):
    """Calculates reliability scores and returns serviceability layers."""
    # Group reviews by suburb
    stats = defaultdict(lambda: {"power": [], "water": []})
    for r in utility_reviews:
        stats[r["suburb"]][r["utility"]].append(r["rating"])

    # Calculate Reliability Index (0-100)
    reliability = {}
    for sub, vals in stats.items():
        p_avg = sum(vals["power"])/len(vals["power"]) if vals["power"] else 4.0 # Default fallback
        w_avg = sum(vals["water"])/len(vals["water"]) if vals["water"] else 4.5
        reliability[sub] = {
            "power_score": round(p_avg * 20),
            "water_score": round(w_avg * 20),
            "power_reviews": len(vals["power"]),
            "water_reviews": len(vals["water"])
        }

    return {
        "reliability": reliability,
        "schools": SCHOOLS,
        "internet": INTERNET_ZONES,
        "projects": INFRASTRUCTURE_PROJECTS
    }

# ── B2B Agent Intelligence Routes ─────────────────────────────────────────────

@app.get("/api/b2b/alerts")
def get_b2b_alerts(current_user: User = Depends(get_current_user)):
    """Find pricing threats from competitors."""
    from png_scraper.b2b_engine import get_competitor_alerts
    # For demo, we'll assume the user is from "The Professionals" or "Ray White PNG"
    # unless they are the admin, then we'll just use "The Professionals"
    agent = "The Professionals"
    if "ray" in (current_user.full_name or "").lower(): agent = "Ray White PNG"

    return {"alerts": get_competitor_alerts(_load_listings(), agent), "agent": agent}

@app.get("/api/b2b/forecasting")
def get_b2b_forecasting(current_user: User = Depends(get_current_user)):
    """Identify high-demand, low-supply opportunities."""
    from png_scraper.b2b_engine import get_demand_forecast
    return {"forecast": get_demand_forecast(_load_listings())}

@app.get("/api/b2b/leads")
def get_b2b_leads(current_user: User = Depends(get_current_user)):
    """Identify hot leads based on platform interaction scoring + Messenger Bot pre-screening."""
    from png_scraper.b2b_engine import get_lead_scoring
    from png_scraper.messenger_bot import get_messenger_leads_demo

    platform_leads = get_lead_scoring()
    messenger_leads = get_messenger_leads_demo()

    # Combine and sort by score
    combined = sorted(platform_leads + messenger_leads, key=lambda x: x["score"], reverse=True)
    return {"leads": combined}

# ── Optional: serve built React SPA from backend (single-service mode) ─────────
# To enable: cd frontend && npm run build && cp -r dist ../backend/static
# Then uncomment:

# ── serve built React SPA from backend (single-service mode) ─────────────────
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR/"assets")), name="assets")
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        return FileResponse(str(STATIC_DIR / "index.html"))
