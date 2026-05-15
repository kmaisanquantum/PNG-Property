# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Prepare the Python backend and final image
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    OUTPUT_FILE=/app/output/png_listings_latest.json \
    HISTORY_FILE=/app/output/suburb_history.json

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Remove any pre-existing static files and copy fresh build from Stage 1
RUN rm -rf /app/static && mkdir -p /app/static
COPY --from=frontend-builder /app/frontend/dist /app/static

# Create directories for persistent data and logs
RUN mkdir -p /app/output /app/uploads /app/data && \
    chmod -R 777 /app/output /app/uploads /app/data

# Expose the application port
EXPOSE 8000

# Start the application using uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
