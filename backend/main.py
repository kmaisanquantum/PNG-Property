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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt

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

STATIC_DIR = Path("static")
SUBURB_COORDS = {
    "Waigani":{"lat":-9.4298,"lng":147.1812},"Boroko":{"lat":-9.4453,"lng":147.1769},
    "Gerehu":{"lat":-9.4736,"lng":147.1609},"Gordons":{"lat":-9.4201,"lng":147.1739},
    "Hohola":{"lat":-9.4512,"lng":147.1651},"Tokarara":{"lat":-9.4580,"lng":147.1700},
    "Koki":{"lat":-9.4721,"lng":147.1847},"Badili":{"lat":-9.4600,"lng":147.1900},
    "Six Mile":{"lat":-9.4150,"lng":147.1500},"Eight Mile":{"lat":-9.3900,"lng":147.1420},
    "Morata":{"lat":-9.4680,"lng":147.1540},"Erima":{"lat":-9.4400,"lng":147.1580},
}

BENCHMARKS = {
    "Waigani":4470,"Boroko":3150,"Gerehu":1880,"Gordons":5957,
    "Hohola":1600,"Tokarara":2275,"Koki":2900,"Badili":3325,
    "Six Mile":1450,"Eight Mile":1225,"Morata":1633,"Erima":2033,
}

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
    auth_provider: str = "email" # email, google, facebook, phone, whatsapp

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    auth_provider: str = "email"

class UserInDB(User):
    hashed_password: Optional[str] = None

users_db: dict[str, UserInDB] = {}

def _load_listings() -> list[dict]:
    db = _get_db()
    if db is not None:
        try:
            docs = list(db["listings"].find({},{"_id":0}).limit(2000))
            if docs: return docs
        except Exception as e:
            log.warning(f"MongoDB query failed: {e}")
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f: return json.load(f)
    return _mock_listings()

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
    user_in_db = UserInDB(
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_password,
        full_name=user.full_name,
        disabled=False,
        auth_provider=user.auth_provider
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
    sources=["Hausples","The Professionals","Ray White PNG","Century 21 PNG","MarketMeri","Facebook Marketplace","SRE PNG","DAC Properties"]
    types=["House","Apartment","Townhouse","Studio","Room","Compound"]
    no_verify={"Facebook Marketplace"}
    TIERS={"Gordons":1,"Waigani":1,"Badili":2,"Boroko":2,"Koki":2,"Tokarara":3,"Gerehu":3,"Hohola":3,"Morata":4,"Erima":4,"Six Mile":4,"Eight Mile":4}
    BASES=[6000,3500,2000,1200]
    rng=random.Random(42); now=datetime.now(timezone.utc); listings=[]
    for i in range(240):
        suburb=rng.choice(suburbs); src=rng.choice(sources); ptype=rng.choice(types)
        beds=rng.choice([1,2,3,4,5]) if ptype not in ("Studio","Room") else 1
        base=BASES[TIERS.get(suburb,3)-1]; price=max(800,int(rng.gauss(base,base*0.18)))
        scraped=now-timedelta(hours=rng.randint(0,72))
        listings.append({"listing_id":f"lst{i:04d}","source_site":src,"title":f"{beds} Bedroom {ptype} – {suburb}",
            "price_raw":f"K{price:,}/month","price_monthly_k":price,"price_confidence":"high",
            "location":f"{suburb}, NCD","suburb":suburb,"listing_url":f"https://hausples.com.pg/listing/{i+1}",
            "is_verified":src not in no_verify,"property_type":ptype,"bedrooms":beds,
            "scraped_at":scraped.isoformat(),"raw_text":f"{beds} bedroom {ptype.lower()} in {suburb} K{price}/month"})
    return listings

def _market_score(price:int,suburb:str)->dict:
    avg=BENCHMARKS.get(suburb,2800); pct=round(((price-avg)/avg)*100,1)
    if pct<=-15: return {"label":"Deal","pct_vs_avg":pct,"color":"#4ade80","benchmark_avg":avg}
    if pct>=15:  return {"label":"Overpriced","pct_vs_avg":pct,"color":"#f87171","benchmark_avg":avg}
    return            {"label":"Fair","pct_vs_avg":pct,"color":"#facc15","benchmark_avg":avg}

def _suburb_stats(listings):
    grouped=defaultdict(list)
    for l in listings:
        if l.get("suburb") and l.get("price_monthly_k"): grouped[l["suburb"]].append(l["price_monthly_k"])
    result=[]
    for suburb,prices in grouped.items():
        srt=sorted(prices); n=len(srt); med=srt[n//2] if n%2 else (srt[n//2-1]+srt[n//2])//2
        c=SUBURB_COORDS.get(suburb,{"lat":-9.44,"lng":147.18})
        result.append({"suburb":suburb,"avg_price":int(sum(prices)/n),"median_price":med,
                        "min_price":min(prices),"max_price":max(prices),"listings":n,"lat":c["lat"],"lng":c["lng"]})
    return sorted(result,key=lambda x:-x["avg_price"])

def _trends(listings):
    top=["Waigani","Boroko","Gerehu"]; now=datetime.now(timezone.utc); rng=random.Random(99); rows=[]
    for w in range(7,-1,-1):
        row={"week":(now-timedelta(weeks=w)).strftime("%b %d")}
        for sub in top:
            all_p=[l["price_monthly_k"] for l in listings if l.get("suburb")==sub and l.get("price_monthly_k")]
            row[sub]=int((sum(all_p)/len(all_p))*rng.uniform(0.93,1.07)) if all_p else BENCHMARKS.get(sub,2500)
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
    user = get_user_by_identifier(token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def _run_scrape(job_id:str, req:ScrapeRequest):
    scrape_jobs[job_id].update({"status":"running","started_at":datetime.now(timezone.utc).isoformat(),"progress":0,"collected":0})
    try:
        rng=random.Random(); total=len(req.sources)*req.max_pages; collected=0
        for i,source in enumerate(req.sources):
            for p in range(req.max_pages):
                await asyncio.sleep(0.8); collected+=rng.randint(8,22)
                scrape_jobs[job_id].update({"progress":int(((i*req.max_pages+p+1)/total)*100),
                    "collected":collected,"current_source":source,"current_page":p+1})
        scrape_jobs[job_id].update({"status":"complete","finished_at":datetime.now(timezone.utc).isoformat(),"progress":100,"collected":collected})
    except Exception as e:
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
        "user": {"email": user.email, "full_name": user.full_name, "phone": user.phone}
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
            "full_name": user.full_name
        }
    }

@app.get("/api/listings")
def get_listings(suburb:Optional[str]=None,source:Optional[str]=None,type:Optional[str]=None,
    min_price:Optional[int]=None,max_price:Optional[int]=None,verified:Optional[bool]=None,
    sort:str="scraped_at",order:str="desc",page:int=1,limit:int=25,
    current_user: User = Depends(get_current_user)):
    ls=_load_listings()
    if suburb: ls=[l for l in ls if (l.get("suburb") or "").lower()==suburb.lower()]
    if source: ls=[l for l in ls if source.lower() in (l.get("source_site") or "").lower()]
    if type:   ls=[l for l in ls if (l.get("property_type") or "").lower()==type.lower()]
    if min_price: ls=[l for l in ls if (l.get("price_monthly_k") or 0)>=min_price]
    if max_price: ls=[l for l in ls if (l.get("price_monthly_k") or 0)<=max_price]
    if verified is not None: ls=[l for l in ls if l.get("is_verified")==verified]
    for l in ls:
        if l.get("price_monthly_k") and l.get("suburb"): l["market_value"]=_market_score(l["price_monthly_k"],l["suburb"])
    try: ls.sort(key=lambda x:x.get(sort) or "",reverse=(order=="desc"))
    except: pass
    total=len(ls); offset=(page-1)*limit
    return {"total":total,"page":page,"pages":max(1,(total+limit-1)//limit),"limit":limit,"listings":ls[offset:offset+limit]}

@app.get("/api/analytics/overview")
def get_overview(current_user: User = Depends(get_current_user)):
    ls=_load_listings(); prices=[l["price_monthly_k"] for l in ls if l.get("price_monthly_k")]
    flags=sum(1 for l in ls if l.get("price_monthly_k") and l.get("suburb") and _market_score(l["price_monthly_k"],l["suburb"])["pct_vs_avg"]>=40)
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
            s=_market_score(l["price_monthly_k"],l["suburb"])
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

@app.get("/api/scrape/jobs")
def list_jobs(current_user: User = Depends(get_current_user)): return {"jobs":sorted(scrape_jobs.values(),key=lambda x:x.get("queued_at",""),reverse=True)[:20]}

@app.get("/api/suburbs")
def get_suburbs(current_user: User = Depends(get_current_user)): return {"suburbs":[{"name":k,"lat":v["lat"],"lng":v["lng"]} for k,v in SUBURB_COORDS.items()]}

@app.get("/api/sources")
def get_source_list(current_user: User = Depends(get_current_user)):
    return {"sources":["Hausples","The Professionals","Ray White PNG","Century 21 PNG",
                       "MarketMeri","SRE PNG","DAC Properties","AAA Properties",
                       "Arthur Strachan","Pacific Palms","Facebook Marketplace"]}

# ── Optional: serve built React SPA from backend (single-service mode) ─────────
# To enable: cd frontend && npm run build && cp -r dist ../backend/static
# Then uncomment:

# ── serve built React SPA from backend (single-service mode) ─────────────────
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR/"assets")), name="assets")
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        return FileResponse(str(STATIC_DIR / "index.html"))
