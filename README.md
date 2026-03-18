# 🏠 PNG Property Intelligence Dashboard

> Papua New Guinea's real-time real estate aggregator, analytics platform, and property intelligence tool.
> Full-stack deployment on **Render** — FastAPI backend + React frontend.

---

## 🗂 Project Structure

```
png-property-dashboard/
│
├── render.yaml                  ← Render Blueprint (deploys both services automatically)
├── .gitignore
├── README.md
│
├── backend/                     ← Render Web Service (Python / FastAPI)
│   ├── main.py                  ← API — 13 endpoints
│   ├── requirements.txt         ← Python dependencies
│   ├── Dockerfile               ← Used if you choose Docker runtime
│   ├── .env.example             ← Copy → .env for local dev
│   └── png_scraper/             ← Scraper engine
│       ├── engine.py
│       ├── normalizer.py
│       ├── market_scorer.py
│       ├── main.py
│       └── scrapers/
│           ├── hausples.py
│           ├── professionals.py
│           ├── general_agency.py
│           └── facebook.py
│
└── frontend/                    ← Render Static Site (React / Vite)
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    ├── .env.example             ← Copy → .env.local for local dev
    ├── public/
    │   ├── _redirects           ← SPA routing for Render Static Site
    │   └── landing.html         ← Public landing page (no build needed)
    └── src/
        ├── App.jsx              ← Full dashboard (5 views, SVG charts)
        └── main.jsx
```

---

## 🚀 Deploy to Render (Recommended: Blueprint)

### Step 1 — Push to GitHub

```bash
cd png-property-dashboard
git init
git add -A
git commit -m "Initial commit — PNG Property Dashboard"
git branch -m main
git remote add origin https://github.com/YOUR_USERNAME/png-property-dashboard.git
git push -u origin main
```

### Step 2 — Deploy with Render Blueprint (one click)

1. Go to **https://dashboard.render.com**
2. Click **New → Blueprint**
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates **both services** automatically:
   - `png-property-api` — FastAPI Web Service
   - `png-property-dashboard` — React Static Site
5. Click **Apply**

Both services deploy in ~3 minutes.

---

### Step 3 — Set Environment Variables

After the first deploy, go to each service in Render dashboard → **Environment**:

#### Backend (`png-property-api`) — Environment tab

| Variable | Value | Notes |
|---|---|---|
| `MONGODB_URL` | `mongodb+srv://...` | From MongoDB Atlas — optional, mock data works without it |
| `REDIS_URL` | `redis://...` | From Upstash — optional |
| `FB_EMAIL` | scraper account email | For live Facebook scraping |
| `FB_PASSWORD` | scraper account password | For live Facebook scraping |
| `JWT_SECRET` | auto-generated | Render generates this automatically from render.yaml |
| `ALLOWED_ORIGINS` | `https://png-property-dashboard.onrender.com` | Your frontend URL |

#### Frontend (`png-property-dashboard`) — Environment tab

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://png-property-api.onrender.com` |

> ⚠️ After setting `VITE_API_URL`, trigger a **Manual Deploy** on the frontend service so the new URL is baked into the build.

---

## 🌐 Your Live URLs

| | URL |
|---|---|
| 🏠 Landing page | `https://png-property-dashboard.onrender.com/landing.html` |
| 📊 Dashboard | `https://png-property-dashboard.onrender.com` |
| 🔌 API | `https://png-property-api.onrender.com` |
| 📖 API docs | `https://png-property-api.onrender.com/api/docs` |

---

## 💻 Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Chromium for Playwright (needed for live scraping)
playwright install chromium

# Copy and edit environment variables
cp .env.example .env
# Edit .env — at minimum the app works with no changes (uses mock data)

# Start the API
uvicorn main:app --reload --port 8000
# API running at http://localhost:8000
# Swagger UI at http://localhost:8000/api/docs
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy and edit environment variables
cp .env.example .env.local
# For local dev, set:  VITE_API_URL=http://localhost:8000
# (vite.config.js proxies /api → localhost:8000 automatically)

# Start Vite dev server
npm run dev
# Dashboard at http://localhost:3000
# Landing page at http://localhost:3000/landing.html
```

---

## 🔌 API Reference

All endpoints are prefixed with `/api`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/listings` | Paginated listings with filters |
| `GET` | `/api/analytics/overview` | KPI summary (totals, avg rent, flags) |
| `GET` | `/api/analytics/heatmap` | Per-suburb price stats + coordinates |
| `GET` | `/api/analytics/trends` | 8-week weekly price trends |
| `GET` | `/api/analytics/supply-demand` | Supply/demand index by suburb |
| `GET` | `/api/analytics/sources` | Listing count by source |
| `GET` | `/api/analytics/middleman-flags` | Overpriced listing report |
| `POST` | `/api/scrape/trigger` | Launch background scrape job |
| `GET` | `/api/scrape/status/{job_id}` | Poll scrape progress |
| `GET` | `/api/scrape/jobs` | List recent jobs |
| `GET` | `/api/suburbs` | Suburb list with lat/lng |
| `GET` | `/api/sources` | Source list |

### Filter listings example
```
GET /api/listings?suburb=Boroko&type=House&min_price=2000&max_price=4000&page=1
```

---

## ⚙️ Render Plan Notes

| Service | Free Plan | Paid Plan ($7/mo Starter) |
|---|---|---|
| Backend | Spins down after 15 min inactivity (cold start ~30s) | Always on |
| Frontend | Always fast (CDN) | Always fast |
| Bandwidth | 100GB/month | Unlimited |

For production, upgrade the backend to **Starter** to avoid cold starts.

---

## 🛠 MongoDB Atlas Setup (Optional but Recommended)

1. Go to **https://mongodb.com/atlas** → Create free cluster
2. Database: `png_realestate`, Collection: `listings`
3. Network Access → Add IP: `0.0.0.0/0` (allow all for Render)
4. Create user → copy connection string
5. Add to Render backend as `MONGODB_URL`

Without MongoDB the app works perfectly using the built-in mock data (240 realistic listings with real suburb pricing).

---

*Built for Papua New Guinea 🇵🇬 by Deeps Systems — Port Moresby property market intelligence.*
