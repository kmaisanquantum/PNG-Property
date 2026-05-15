# 🚀 Deploying to Coolify

To successfully deploy this project on Coolify, follow these steps to ensure the correct build system is used.

## 1. Change the Build Pack
By default, Coolify might attempt to use **Nixpacks**, which fails because this is a monorepo. You must switch to **Dockerfile**.

1. Go to your Service in the Coolify Dashboard.
2. Navigate to **Settings** -> **Build Pack**.
3. Select **Dockerfile** from the dropdown.
4. Set the **Dockerfile Path** to `./Dockerfile` (it is located in the root directory).

## 2. Environment Variables
Ensure the following environment variables are set in the **Environment Variables** tab:

| Variable | Value | Notes |
|---|---|---|
| `PORT` | `8000` | Coolify usually sets this automatically, but ensure it matches. |
| `VITE_API_URL` | `/api` | Used by the React build to proxy requests to the backend. |

## 3. Why was this failing?
The deployment was failing because:
- Nixpacks was confused by an orphaned `package-lock.json` in the root directory.
- Nixpacks could not automatically detect the mixed Python/Node.js environment of this monorepo.

The provided root `Dockerfile` uses a multi-stage build to correctly compile the React frontend and serve it via the FastAPI backend.
