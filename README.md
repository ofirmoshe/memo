# Memora - AI-powered Personal Memory Assistant

Memora is an AI-powered personal memory assistant that helps users save, organize, and retrieve online content effortlessly.

## Features

- Extract and analyze content from URLs
- Organize and index content in a structured database
- Retrieve content using natural language queries
- Support for social media and general websites
- Intelligent content type detection

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- PostgreSQL (for production) or SQLite (for development)
- Docker (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd memo
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   
4. Edit `.env` file and add your OpenAI API key and database configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   
   # For local development with SQLite:
   DATABASE_URL=sqlite:///./memora.db
   
   # For PostgreSQL:
   # DATABASE_URL=postgresql://username:password@localhost:5432/memora
   ```

5. Initialize the database and run migrations:
   ```bash
   python -m app.cli db-migrate --init
   ```

## Running Locally

### Running the API Server

```bash
python -m app.main
```

Or via uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

The API server will be available at `http://localhost:8001`.

### Using the CLI

Save a URL:
```bash
python -m app.cli save <user_id> <url>
```

Search for content:
```bash
python -m app.cli search <user_id> <query>
```

Show version:
```bash
python -m app.cli version
```

## Docker Setup

### Building the Docker Image

```bash
docker build -t memora .
```

### Running with Docker

```bash
docker run -d -p 8001:8001 --name memora-app \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -v $(pwd)/data:/app/data \
  memora
```

### Using Docker Compose

1. Set up your environment variables in the `.env` file
2. Run with docker-compose:
   ```bash
   docker-compose up -d
   ```

## Testing Endpoints

### API Documentation

Access the Swagger UI documentation at:
```
http://localhost:8001/docs
```

### Testing with cURL

Health check:
```bash
curl -X GET "http://localhost:8001/health"
```

Save URL (replace with your values):
```bash
curl -X POST "http://localhost:8001/extract_and_save" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "url": "https://example.com"}'
```

Search content:
```bash
curl -X GET "http://localhost:8001/search?user_id=user1&query=example&top_k=5"
```

Search with filters:
```bash
curl -X GET "http://localhost:8001/search?user_id=user1&query=video&content_type=social_media&platform=youtube"
```

### Testing with PowerShell

Health check:
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8001/health" | Select-Object -ExpandProperty Content
```

Save URL:
```powershell
$body = @{
    user_id = "user1"
    url = "https://example.com"
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:8001/extract_and_save" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

Search content:
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8001/search?user_id=user1&query=example&top_k=5" | Select-Object -ExpandProperty Content
```

## Troubleshooting

- If you encounter database errors, try running the migration script:
  ```bash
  python -m app.cli db-migrate
  ```

- For Docker volume permission issues, ensure the data directory has appropriate permissions:
  ```bash
  mkdir -p data
  chmod 777 data  # On Linux/macOS
  ```

## Database Configuration

### Using SQLite (Development)

SQLite is the default database for development. No additional configuration is required.

### Using PostgreSQL (Production)

For production environments, PostgreSQL is recommended:

1. Install PostgreSQL on your system or use a cloud provider
2. Create a database and user:
   ```sql
   CREATE DATABASE memora;
   CREATE USER memora_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE memora TO memora_user;
   ```
3. Update your `.env` file with the PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://memora_user:your_password@localhost:5432/memora
   ```

### Database Migrations

Memora uses Alembic for database migrations:

```bash
# Initialize migrations (first time only)
python -m app.cli db-migrate --init

# Run migrations
python -m app.cli db-migrate

# Create a new migration
python -m app.cli create-migration "Description of changes"
```

## Cloud Deployment

### Preparing for Cloud Deployment

1. Set up a PostgreSQL database on your cloud provider (AWS RDS, Azure Database, Google Cloud SQL, etc.)

2. Update your environment variables with the cloud database connection string:
   ```
   DATABASE_URL=postgresql://username:password@your-instance.region.rds.amazonaws.com:5432/memora
   ```

3. Configure connection pooling settings if needed:
   ```
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   DB_POOL_RECYCLE=1800
   ```

### Kubernetes Deployment

The `k8s` directory contains Kubernetes manifests for deploying Memora to a Kubernetes cluster:

1. Update the ConfigMap and Secret with your environment variables
2. Apply the manifests:
   ```bash
   kubectl apply -f k8s/
   ```