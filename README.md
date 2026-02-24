# 🏠 PNG Property Dashboard

> **Papua New Guinea's first real-time real estate aggregator and analytics platform.**
> Scrapes, normalises, scores and visualises rental listings from 10+ PNG sources.

[![CI/CD](https://github.com/YOUR_USERNAME/png-property-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/png-property-dashboard/actions)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

---

## 📸 Screenshots

| Landing Page | Dashboard | Heatmap |
|---|---|---|
| Multi-auth landing with analytics preview | Live KPI cards + trend charts | Interactive suburb price bubble map |

---

## ✨ Features

### 🔍 Data Aggregation
- Scrapes **10+ PNG real estate sources** simultaneously using Playwright
- Sources: Hausples, The Professionals, Ray White PNG, Century 21, MarketMeri, SRE, DAC, AAA Properties, Arthur Strachan, Pacific Palms, **Facebook Marketplace**
- Stealth browser with anti-detection (canvas noise, webdriver spoofing, Gaussian delays)
- 6-hour automated refresh cycle

### 📊 Analytics Engine
- **Market Value Scorer** — every listing tagged Deal 🟢 / Fair 🟡 / Overpriced 🔴
- **Middleman Detector** — flags listings ≥40% above suburb formal-site average
- **Price Normaliser** — converts all formats (`K500/week`, `PGK1200 fortnight`, `1800 kina`) to monthly PGK
- **Supply/Demand Index** — per-suburb rental pressure analysis
- **8-week Price Trends** — historical tracking for top suburbs

### 🗺 Interactive Heatmap
- SVG bubble map of Port Moresby suburbs colour-coded by average rent
- Clickable suburb detail panels
- Real lat/lng coordinates for all 12 NCD suburbs

### 🔐 Authentication
- Email / Password
- Phone OTP (SMS)
- WhatsApp OTP
- Google OAuth
- Facebook OAuth
- Apple Sign-In

### 🚀 Infrastructure
- FastAPI backend with 10 REST endpoints
- Background scrape jobs with live progress polling
- MongoDB Atlas (flexible schema for social media data)
- Redis job queue and caching
- Docker Compose for one-command local start
- GitHub Actions CI/CD → Railway + Vercel

---

## 🏗 Project Structure

```
png-property-dashboard/
│
├── 🐍 backend/                    FastAPI + Scraper Engine
│   ├── main.py                    API routes (10 endpoints)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── png_scraper/               Scraper Engine Package
│       ├── engine.py              Abstract base, stealth browser, normaliser
│       ├── main.py                Orchestrator (runs all scrapers)
│       ├── normalizer.py          Price/suburb/type parsers
│       ├── market_scorer.py       Deal/Fair/Overpriced scoring
│       └── scrapers/
│           ├── hausples.py        HausplesScraper (React SPA)
│           ├── professionals.py   ProfessionalsScraper (WordPress)
│           ├── general_agency.py  GeneralAgencyScraper (8 agency sites)
│           └── facebook.py        FacebookScraper (stealth + OTP login)
│
├── ⚛️  frontend/                   React 18 + Vite SPA
│   ├── src/
│   │   ├── App.jsx                Complete dashboard (5 views, 742 lines)
│   │   └── main.jsx
│   ├── public/
│   │   └── landing-page.html      Standalone landing page (no build needed)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── nginx.conf
│
├── 📋 docs/
│   └── ARCHITECTURE.md            System design & data flow
│
├── ⚙️  .github/
│   └── workflows/ci.yml           GitHub Actions CI/CD
│
├── docker-compose.yml             One-command full stack launch
├── .env.example                   Environment variable template
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Option A — Docker (Recommended, one command)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/png-property-dashboard.git
cd png-property-dashboard

# 2. Set up environment
cp .env.example .env
# Edit .env with your values (MongoDB, Redis, optional FB credentials)

# 3. Launch everything
docker compose up --build

# ✅ Access:
# Landing page  →  http://localhost:3000/landing-page.html
# Dashboard     →  http://localhost:3000
# API           →  http://localhost:8000
# API Docs      →  http://localhost:8000/docs
```

### Option B — Local Development (no Docker)

```bash
# ── Backend ─────────────────────────────────────────
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp ../.env.example ../.env
uvicorn main:app --reload --port 8000

# ── Frontend (new terminal) ──────────────────────────
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/listings` | Paginated listings with filters |
| `GET` | `/api/analytics/overview` | KPI summary (totals, avg rent, flags) |
| `GET` | `/api/analytics/heatmap` | Per-suburb price stats |
| `GET` | `/api/analytics/trends` | Weekly price trends (8 weeks) |
| `GET` | `/api/analytics/supply-demand` | Supply/demand by suburb |
| `GET` | `/api/analytics/sources` | Listing count by source |
| `GET` | `/api/analytics/middleman-flags` | Flagged overpriced listings |
| `POST` | `/api/scrape/trigger` | Launch background scrape job |
| `GET` | `/api/scrape/status/{job_id}` | Poll scrape job progress |
| `GET` | `/api/scrape/jobs` | List recent scrape jobs |

Full interactive docs: `http://localhost:8000/docs`

### Example: Filter listings

```bash
curl "http://localhost:8000/api/listings?suburb=Boroko&type=House&min_price=2000&max_price=4000&page=1"
```

### Example: Trigger a scrape

```bash
curl -X POST http://localhost:8000/api/scrape/trigger \
  -H "Content-Type: application/json" \
  -d '{"sources":["hausples","professionals"],"max_pages":3}'
```

---

## 🧠 Scraper Architecture

```
Sources (10+)              Scraper Layer              Analytics
─────────────              ─────────────              ─────────
Hausples        ──►  HausplesScraper       ──►  normalise_price()
The Professionals ──►  ProfessionalsScraper  ──►  detect_suburb()
8 Agency Sites  ──►  GeneralAgencyScraper  ──►  classify_type()
Facebook Market ──►  FacebookScraper       ──►  score_market_value()
                                           ──►  flag_middleman()
                          │                         │
                    deduplicate()            MongoDB Atlas
                          │                         │
                    FastAPI REST API  ◄──────────────┘
                          │
                    React Dashboard
```

### Stealth Features (Facebook)
- Removes `navigator.webdriver` flag
- Fakes plugin list, languages, WebGL vendor
- Canvas fingerprint noise injection
- Gaussian-distributed random delays (not detectable as uniform)
- Mouse movement simulation
- Session persistence (`fb_session.json`) to avoid re-login bans

---

## 📊 Data Model

Every listing is a normalised `Listing` record:

```json
{
  "listing_id":       "a3f8cd71e2b94f1c",
  "source_site":      "Hausples",
  "title":            "3 Bedroom House – Boroko",
  "price_raw":        "K2,500/month",
  "price_monthly_k":  2500,
  "price_confidence": "high",
  "location":         "Boroko, NCD",
  "suburb":           "Boroko",
  "listing_url":      "https://hausples.com.pg/property/...",
  "is_verified":      true,
  "property_type":    "House",
  "bedrooms":         3,
  "scraped_at":       "2025-02-24T04:30:00Z",
  "market_value": {
    "label":          "Fair",
    "pct_vs_avg":     -1.6,
    "benchmark_avg":  2541
  }
}
```

---

## ☁️ Production Deployment

### Railway (Backend) + Vercel (Frontend)

```bash
# Backend → Railway
npm install -g @railway/cli
railway login
railway link
railway up

# Set Railway environment variables:
# MONGODB_URL, REDIS_URL, FB_EMAIL, FB_PASSWORD, JWT_SECRET

# Frontend → Vercel
npm install -g vercel
cd frontend
vercel --prod
```

### Environment Variables Required

| Variable | Description |
|----------|-------------|
| `MONGODB_URL` | MongoDB Atlas connection string |
| `REDIS_URL` | Redis / Upstash connection string |
| `FB_EMAIL` | Dedicated Facebook scraper account email |
| `FB_PASSWORD` | Facebook scraper account password |
| `JWT_SECRET` | 64-char random string for auth tokens |
| `FRONTEND_URL` | Frontend URL for CORS (e.g. `https://your-app.vercel.app`) |

---

## ⚠️ Facebook Scraping — Safety Rules

1. **NEVER use your personal Facebook account** — use a dedicated scraper account
2. Create a separate Gmail → Facebook account purely for scraping
3. Enable TOTP 2FA on the scraper account (so you control checkpoints)
4. Use a residential IP in PNG (or a proxy close to Port Moresby)
5. Sessions are saved to `fb_session.json` — reused to minimise login frequency
6. Rotate the scraper account every 30–60 days

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, pure CSS + SVG (zero UI library deps) |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Scraping** | Playwright (Chromium), stealth JS injection |
| **Database** | MongoDB 7 (Atlas in production) |
| **Queue** | Redis 7 (Upstash in production) |
| **Auth** | JWT + OAuth (Google, Facebook, Apple) + OTP |
| **CI/CD** | GitHub Actions → Railway + Vercel |
| **Container** | Docker Compose |

---

## 📄 License

MIT License — free to use, modify and distribute.

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

*Built for Papua New Guinea 🇵🇬 — Port Moresby property market intelligence.*
