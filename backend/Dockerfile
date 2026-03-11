FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
# Paths are now relative to the 'backend' directory
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure output directory exists
RUN mkdir -p output

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Use shell form to allow environment variable expansion
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
