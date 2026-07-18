# ==============================================================================
# MIRROR CITY Backend Production Dockerfile
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for building some Python packages (e.g. gcc, sqlite3)
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose backend port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Run database migrations/seeding before starting server
# We run startup script to ensure SQLite DB has seeded data
CMD python database/seed.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000
