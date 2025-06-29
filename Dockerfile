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

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"] 