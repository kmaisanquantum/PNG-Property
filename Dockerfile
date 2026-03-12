FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
# We use the backend/requirements.txt directly
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into the container
# We copy from the backend directory to the /app directory
COPY backend/ .

# Ensure output directory exists for scrapers
RUN mkdir -p output

# Expose the port the app runs on (Render uses PORT env var)
EXPOSE 8000

# Command to run the application
# Start from main.py which is now in /app
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
