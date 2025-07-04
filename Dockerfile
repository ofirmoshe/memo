FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client and yt-dlp dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Explicitly install psycopg2-binary first
RUN pip install --no-cache-dir psycopg2-binary

# Then install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port for FastAPI (Railway will use PORT env var, local uses 8001)
EXPOSE 8001
ENV PORT=8001

# Set environment variables
ENV PYTHONPATH=/app
ENV USER_PROFILES_ENABLED=true

# Default command - use Railway startup script for both web and bot
CMD ["python", "start_railway.py"] 