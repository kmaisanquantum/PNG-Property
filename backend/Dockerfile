FROM python:3.12-slim

# System deps for Playwright (Chromium) + curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
    libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
    xdg-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output

# Render injects PORT env var automatically
ENV PORT=8000

EXPOSE 8000

# Start uvicorn — uses $PORT so Render can override
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
