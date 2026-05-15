# 🚀 Deploying to Coolify

To successfully deploy this project on Coolify, follow these steps to ensure the correct build system is used.

## 1. Preferred Method: Dockerfile
Switching to the **Dockerfile** build pack is the most reliable way to deploy this monorepo.

1. Go to your Service in the Coolify Dashboard.
2. Navigate to **Settings** -> **Build Pack**.
3. Select **Dockerfile** from the dropdown.
4. Set the **Dockerfile Path** to `./Dockerfile`.
5. Click **Save**.

## 2. Fallback Method: Nixpacks
The project includes a root `requirements.txt` and `nixpacks.toml` to support Nixpacks.

1. Set the **Build Pack** to **Nixpacks**.
2. Set the **Base Directory** to `/` (the root).
3. Nixpacks will detect the Python environment and use the custom configuration in `nixpacks.toml` to build the frontend as well.

## 3. Environment Variables
Ensure the following variables are set in the **Environment Variables** tab:

| Variable | Value | Notes |
|---|---|---|
| `PORT` | `8000` | Internal port (Docker EXPOSE). |
| `VITE_API_URL` | `/api` | Crucial for the React frontend build. |
| `SECRET_KEY` | `some-random-secret` | For JWT authentication. |

## 4. Persistent Storage (Crucial)
This app generates listing data and stores Facebook sessions. In Coolify:
1. Go to **Storage**.
2. Add a new **Persistent Storage** (Volume).
3. Mount Path: `/app/output` (for listing JSON files).
4. Mount Path: `/app/data` (for scraper sessions).
5. Mount Path: `/app/uploads` (for user documents).
