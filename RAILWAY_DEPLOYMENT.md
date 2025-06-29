# Railway Deployment Guide for Memora

This guide will help you deploy Memora to Railway while keeping it compatible with local development.

## Prerequisites

1. **GitHub Repository**: Your code should be pushed to GitHub
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Environment Variables**: You'll need your OpenAI API key and Telegram bot token

## Step-by-Step Deployment

### 1. Prepare Your Repository

Your repository is already configured for Railway deployment with:
- ✅ `railway.json` - Railway configuration
- ✅ `start_railway.py` - Railway-specific startup script
- ✅ `Dockerfile` - Updated for Railway compatibility
- ✅ Dynamic backend URL detection in `telegram_bot.py`

### 2. Deploy to Railway

1. **Go to [railway.app](https://railway.app) and sign in**

2. **Create a new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Memora repository

3. **Add PostgreSQL Database:**
   - In your Railway project dashboard
   - Click "New Service" → "Database" → "PostgreSQL"
   - Railway will automatically create the database and set `DATABASE_URL`

4. **Configure Environment Variables:**
   - Go to your main service (not the database)
   - Click on "Variables" tab
   - Add these environment variables:

   ```
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   TELEGRAM_BOT_TOKEN=your-actual-telegram-bot-token-here
   ```

   **Note**: Railway automatically provides:
   - `DATABASE_URL` (from PostgreSQL service)
   - `PORT` (assigned by Railway)
   - `RAILWAY_ENVIRONMENT=production`

5. **Add Railway Volume (Optional for file storage):**
   - If you need persistent file storage beyond the database
   - Go to your main service settings
   - Click "Volumes" tab
   - Add a volume with mount path `/app/data`
   - This provides persistent storage for uploaded files

### 3. Deploy and Monitor

1. **Automatic Deployment:**
   - Railway will automatically build and deploy your app
   - Monitor the build logs in the Railway dashboard

2. **Check Deployment:**
   - Once deployed, you'll get a URL like `https://your-app-name.railway.app`
   - Visit `https://your-app-name.railway.app/health` to verify the API is running

3. **Test Telegram Bot:**
   - Your Telegram bot should now be running on Railway
   - Send a message to your bot to test functionality

## Persistent Storage on Railway

### Database Storage
- All user data, content, and metadata are stored in the PostgreSQL database
- Railway's managed PostgreSQL provides automatic backups and persistence

### File Storage (Optional)
- For uploaded files (images, documents), you can add a Railway volume:
  1. Go to your service settings in Railway dashboard
  2. Navigate to "Volumes" tab  
  3. Add volume with mount path: `/app/data`
  4. This creates persistent storage that survives deployments

### Alternative: Cloud Storage
- For production, consider using cloud storage (AWS S3, Google Cloud Storage)
- More scalable than local file storage
- Can be integrated by updating file upload endpoints

## Environment Variable Details

### Required Variables (Set these in Railway)
- `OPENAI_API_KEY`: Your OpenAI API key for content analysis
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from @BotFather

### Automatically Set by Railway
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Port number assigned by Railway
- `RAILWAY_ENVIRONMENT`: Set to "production"

### Optional Variables
- `BACKEND_URL`: Override if needed (usually not required)

## Local Development Compatibility

Your local development setup remains unchanged:

### Using Docker Compose (Recommended for local)
```bash
# This still works exactly as before
docker-compose up -d
```

### Using Python directly
```bash
# Backend
python -m app.main

# Telegram bot (in another terminal)
python telegram_bot.py
```

## How the Environment Detection Works

The app automatically detects the environment:

1. **Railway**: Detects `RAILWAY_ENVIRONMENT` → uses localhost communication
2. **Docker Compose**: Detects PostgreSQL in `DATABASE_URL` → uses service names
3. **Local Development**: Falls back to localhost

## Troubleshooting

### Build Issues
- Check Railway build logs for errors
- Ensure all required files are committed to GitHub
- Verify Dockerfile doesn't use banned keywords (like `VOLUME`)

### Database Issues
- Verify PostgreSQL service is running in Railway
- Check that `DATABASE_URL` is automatically set

### Bot Not Responding
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check Railway service logs for errors
- Ensure both backend and bot processes are running

### Environment Variable Issues
- Double-check variable names (case-sensitive)
- Ensure no extra spaces in values
- Verify OpenAI API key is valid

## Scaling and Costs

### Free Tier
- Railway provides $5/month in credits
- Should cover development and testing

### Production Scaling
- Railway automatically scales based on usage
- Pay-as-you-grow pricing
- Monitor usage in Railway dashboard

## Updating Your Deployment

1. **Push changes to GitHub**
2. **Railway automatically redeploys**
3. **Monitor deployment in Railway dashboard**

## Support

If you encounter issues:
1. Check Railway documentation: [docs.railway.app](https://docs.railway.app)
2. Review Railway service logs
3. Verify environment variables are set correctly

## Architecture on Railway

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

Both the FastAPI backend and Telegram bot run in the same container, communicating via localhost, while connecting to the managed PostgreSQL database. 