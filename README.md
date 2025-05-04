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
   
4. Edit `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Run database migrations (if upgrading from a previous version):
   ```bash
   python -m app.cli db-migrate
   ```

## Running Locally

### Running the API Server

```bash
python -m app.main
```

Or via uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API server will be available at `http://localhost:8000`.

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
docker run -d -p 8000:8000 --name memora-app \
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
http://localhost:8000/docs
```

### Testing with cURL

Health check:
```bash
curl -X GET "http://localhost:8000/health"
```

Save URL (replace with your values):
```bash
curl -X POST "http://localhost:8000/extract_and_save" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "url": "https://example.com"}'
```

Search content:
```bash
curl -X GET "http://localhost:8000/search?user_id=user1&query=example&top_k=5"
```

Search with filters:
```bash
curl -X GET "http://localhost:8000/search?user_id=user1&query=video&content_type=social_media&platform=youtube"
```

### Testing with PowerShell

Health check:
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8000/health" | Select-Object -ExpandProperty Content
```

Save URL:
```powershell
$body = @{
    user_id = "user1"
    url = "https://example.com"
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:8000/extract_and_save" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

Search content:
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8000/search?user_id=user1&query=example&top_k=5" | Select-Object -ExpandProperty Content
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