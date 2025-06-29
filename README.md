# Memora - AI-powered Personal Memory Assistant

Memora is an AI-powered personal memory assistant that helps users save, organize, and retrieve online content effortlessly.

## Features

- Extract and analyze content from URLs
- Organize and index content in a structured database
- Retrieve content using natural language queries
- Support for social media and general websites
- Intelligent content type detection

## Deployment Options

### 🚀 Railway Deployment (Recommended for Production)

Deploy to Railway for a stable, scalable cloud deployment:

1. **Quick Deploy**: Follow the detailed guide in [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
2. **One-Click Setup**: Import from GitHub → Add PostgreSQL → Set environment variables
3. **Auto-Scaling**: Automatically scales with your user base
4. **Cost-Effective**: Free tier covers testing, pay-as-you-grow

**Required Environment Variables for Railway:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token

Railway automatically provides `DATABASE_URL` and `PORT`.

### 🐳 Local Docker Development

For local development and testing:

```bash
# Clone and setup
git clone <repository-url>
cd memo
cp .env.example .env
# Edit .env with your API keys

# Run with Docker Compose
docker-compose up -d
```

### 🔧 Local Python Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -m app.cli db-migrate --init

# Run backend
python -m app.main

# Run telegram bot (in another terminal)
python telegram_bot.py
```

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- Telegram Bot Token (from @BotFather)
- PostgreSQL (for production) or SQLite (for development)

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
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   
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
  -e TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here \
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

## Environment Detection

The application automatically detects the deployment environment:

- **Railway**: Detects `RAILWAY_ENVIRONMENT` → uses localhost communication
- **Docker Compose**: Detects PostgreSQL in `DATABASE_URL` → uses service names  
- **Local Development**: Falls back to localhost

Test environment detection:
```bash
python test_environment.py
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

For production environments, PostgreSQL is recommended. Railway automatically provides a managed PostgreSQL instance.

## Architecture

### Local Development
```
┌─────────────┐    ┌───────────────┐    ┌─────────────┐
│   FastAPI   │    │ Telegram Bot  │    │ PostgreSQL  │
│   Backend   │    │               │    │  Database   │
│   :8001     │◄──►│               │◄──►│   :5432     │
└─────────────┘    └───────────────┘    └─────────────┘
```

### Railway Deployment
```
┌─────────────────────────────────────┐
│           Railway Service           │
├─────────────────────────────────────┤
│  ┌─────────────┐ ┌───────────────┐  │
│  │   FastAPI   │ │ Telegram Bot  │  │
│  │   Backend   │ │               │  │
│  │   :8080     │ │               │  │
│  └─────────────┘ └───────────────┘  │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│        PostgreSQL Database         │
│         (Railway Service)          │
└─────────────────────────────────────┘
```