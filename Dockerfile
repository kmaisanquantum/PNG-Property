# Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Use production API URL or fallback to /api for proxying
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Build backend and final image
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from builder stage to the backend static directory
COPY --from=frontend-builder /app/frontend/dist /app/static

# Ensure output directory exists for scrapers
RUN mkdir -p output

# Expose the port the app runs on (Render uses PORT env var)
EXPOSE 8000

# Command to run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
