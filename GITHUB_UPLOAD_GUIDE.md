# 📤 How to Upload PNG Property Dashboard to GitHub

## Step 1 — Create a GitHub Repository

1. Go to **https://github.com/new**
2. Fill in:
   - **Repository name:** `png-property-dashboard`
   - **Description:** `PNG's first real-time real estate aggregator and analytics platform`
   - **Visibility:** Public (or Private)
   - ❌ Do NOT tick "Add a README" (we already have one)
3. Click **Create repository**

---

## Step 2 — Upload via GitHub Web UI (Easiest)

1. On your new empty repo page, click **"uploading an existing file"**
2. **Unzip** `png-property-dashboard.zip` on your computer first
3. Drag the entire **`png-property-dashboard/`** folder contents into the upload area
4. Scroll down, set commit message: `🏠 Initial release — PNG Property Dashboard v1.0.0`
5. Click **Commit changes**

> ⚠️ GitHub web upload has a 100-file limit. If it fails, use the Git CLI method below.

---

## Step 3 — Upload via Git CLI (Recommended)

```bash
# 1. Unzip the downloaded file
unzip png-property-dashboard.zip
cd png-property-dashboard

# 2. Add your GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/png-property-dashboard.git

# 3. Rename branch to main (GitHub standard)
git branch -m master main

# 4. Push to GitHub
git push -u origin main
```

That's it — one push and your full history is on GitHub.

---

## Step 4 — Set Repository Secrets (for CI/CD)

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets for GitHub Actions to deploy automatically:

| Secret Name | Value |
|---|---|
| `RAILWAY_TOKEN` | Get from https://railway.app/account/tokens |
| `VERCEL_TOKEN` | Get from https://vercel.com/account/tokens |
| `VERCEL_ORG_ID` | From `vercel link` command output |
| `VERCEL_PROJECT_ID` | From `vercel link` command output |

---

## Step 5 — Deploy Backend to Railway

1. Go to **https://railway.app** → New Project → Deploy from GitHub repo
2. Select `png-property-dashboard`
3. Set **Root Directory** to `backend`
4. Add environment variables (from your `.env`):
   - `MONGODB_URL` (get free cluster at mongodb.com/atlas)
   - `REDIS_URL` (get free instance at upstash.com)
   - `FB_EMAIL`, `FB_PASSWORD`
   - `JWT_SECRET`
   - `FRONTEND_URL` (your Vercel URL, set after next step)

---

## Step 6 — Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# From the project root
cd frontend
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: png-property-dashboard
# - Root: ./
# - Build command: npm run build
# - Output dir: dist
```

Or connect via **https://vercel.com/new** → Import Git Repository.

Set environment variable in Vercel:
- `VITE_API_URL` = your Railway backend URL (e.g. `https://your-api.railway.app`)

---

## Step 7 — Enable GitHub Actions

Actions run automatically on every push to `main`. Check:
- **Actions tab** on your repo → you'll see the CI pipeline running
- It tests the Python engine, builds the React frontend, and checks Docker Compose

To trigger manually:
```
Actions → CI/CD → Run workflow
```

---

## 🎉 Your live URLs will be:

| Service | URL |
|---|---|
| Landing Page | `https://your-app.vercel.app/landing-page.html` |
| Dashboard | `https://your-app.vercel.app` |
| API | `https://your-api.railway.app` |
| API Docs | `https://your-api.railway.app/docs` |

---

## Quick Reference — git commands after setup

```bash
# After making changes, push updates:
git add -A
git commit -m "feat: describe your change"
git push

# GitHub Actions will automatically test and deploy
```
