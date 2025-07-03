# Railway Deployment Guide for Memora with User Profiles

This guide covers deploying Memora to Railway with the complete user profile system.

## Features Included in Railway Deployment

### ✅ Core Memora Features
- AI-powered content extraction and analysis
- Multi-format file support (PDFs, Word docs, images)
- Semantic search with embeddings
- Telegram bot integration
- RESTful API endpoints

### ✅ Enhanced User Profile System
- **Multi-provider authentication** (Telegram, Google, Apple ready)
- **Rich user profiles** with preferences and settings
- **Activity tracking** and analytics
- **Usage statistics** and insights
- **Auto-migration** on Railway deployment
- **Backward compatibility** with existing data

## Quick Deploy to Railway

### Option 1: Deploy Button (Recommended)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/memora-with-profiles)

### Option 2: Manual Deployment

1. **Fork this repository** to your GitHub account

2. **Connect to Railway:**
   - Visit [Railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository

3. **Add Environment Variables:**
   ```
   # Required
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional (defaults provided)
   USER_PROFILES_ENABLED=true
   PYTHONPATH=/app
   ```

4. **Deploy:**
   - Railway will automatically detect the Dockerfile
   - First deployment takes 3-5 minutes
   - User profile tables are auto-created on first run

## Environment Variables

### Required Variables
- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather)
- `OPENAI_API_KEY`: Get from [OpenAI Dashboard](https://platform.openai.com/api-keys)

### Railway Auto-Provided
- `DATABASE_URL`: PostgreSQL connection string (auto-generated)
- `PORT`: Application port (auto-assigned)
- `RAILWAY_ENVIRONMENT`: Deployment environment flag

### Optional Configuration
```env
# User Profile System
USER_PROFILES_ENABLED=true          # Enable user profiles (default: true)

# Application Settings
PYTHONPATH=/app                      # Python module path
LOG_LEVEL=INFO                       # Logging verbosity

# File Processing
MAX_FILE_SIZE=50                     # Maximum file size in MB
EMBEDDING_DIMENSION=1536             # OpenAI embedding dimension
```

## Database Configuration

### PostgreSQL Service
Railway automatically provides:
- ✅ **PostgreSQL 14+** with persistent storage
- ✅ **Automatic backups** and point-in-time recovery
- ✅ **Connection pooling** for performance
- ✅ **SSL encryption** for security

### User Profile Tables
Automatically created on first deployment:
- `user_profiles` - Extended user information and preferences
- `user_auth_providers` - Multi-platform authentication tracking
- `user_activity` - Activity logs and analytics

### Migration Process
```
1. Railway starts the container
2. FastAPI app initializes
3. Database connection established
4. Auto-migration checks for user profile tables
5. Tables created if not present (safe operation)
6. App ready to receive requests
```

## Deployment Process

### Automatic Deployment Pipeline
```
1. Push to GitHub → Railway detects changes
2. Build Docker image with all dependencies
3. Deploy with zero-downtime rolling update
4. Run database migrations if needed
5. Start FastAPI server and Telegram bot
6. Health checks confirm deployment success
```

### Build Optimization
- **Multi-stage Docker build** for smaller images
- **Dependency caching** for faster rebuilds
- **Production-optimized** Python environment

## API Endpoints

### Core Memora API
```
POST   /extract          # Extract content from URLs
POST   /save-text        # Save text content
POST   /save-file        # Save file content
POST   /search           # Semantic search
GET    /user/{id}/stats  # User statistics
GET    /health           # Health check
```

### User Profile API (New!)
```
# Profile Management
GET    /api/profiles/{user_id}           # Get user profile
POST   /api/profiles/                    # Create profile
PUT    /api/profiles/{user_id}           # Update profile
DELETE /api/profiles/{user_id}           # Delete profile

# Provider-Specific Creation
POST   /api/profiles/telegram            # Create from Telegram data
POST   /api/profiles/google              # Create from Google data
POST   /api/profiles/apple               # Create from Apple data

# Activity & Analytics
POST   /api/profiles/{user_id}/activity  # Track user activity
GET    /api/profiles/{user_id}/stats     # Get user statistics
GET    /api/profiles/{user_id}/summary   # Get profile summary

# Batch Operations
POST   /api/profiles/batch               # Batch operations
GET    /api/profiles/search              # Search profiles
```

## Telegram Bot Features

### Enhanced Commands
```
/start    - Welcome message with profile setup
/search   - Explicit search command
/stats    - Enhanced statistics with profile data
/profile  - View personal profile information (NEW!)
```

### Smart Message Processing
- **Intent detection** - Automatically understands save vs search
- **Multi-language support** - Translates and processes various languages
- **Activity tracking** - Records all interactions for analytics
- **Profile integration** - Personalizes responses based on user data

## Monitoring & Analytics

### Built-in Health Checks
- `GET /health` - Basic health status
- `GET /health/detailed` - Comprehensive system status including:
  - Database connectivity
  - User profile system status
  - Memory and CPU usage
  - Active user statistics

### User Analytics
Access via the user profile API:
- **Usage patterns** - When and how users interact
- **Content preferences** - What types of content users save most
- **Search behavior** - Query patterns and success rates
- **Engagement metrics** - Daily/weekly/monthly active users

## Security Features

### Data Protection
- ✅ **Encrypted connections** (HTTPS/WSS)
- ✅ **Environment variable security** (secrets not in code)
- ✅ **Database encryption** at rest
- ✅ **User data isolation** (strict user_id filtering)

### Authentication Security
- ✅ **Multi-provider support** (Telegram, Google, Apple)
- ✅ **Provider verification** (validates tokens/signatures)
- ✅ **Session management** (tracks authentication state)
- ✅ **Privacy controls** (user-configurable privacy settings)

## Scaling & Performance

### Railway Scaling
- **Automatic scaling** based on traffic
- **Load balancing** across multiple instances
- **Regional deployment** for low latency
- **CDN integration** for static assets

### Database Optimization
- **Indexed queries** for fast user lookups
- **Connection pooling** for concurrent users
- **Query optimization** for large datasets
- **JSON columns** for flexible data storage

## Troubleshooting

### Common Issues

#### Migration Problems
```bash
# Check migration status
curl https://your-app.railway.app/health/detailed

# Look for:
"user_profiles_available": true
"migration_status": "completed"
```

#### Bot Connection Issues
```bash
# Check bot status in Railway logs
# Look for: "Starting enhanced Telegram bot with user profiles..."

# Verify environment variables
TELEGRAM_BOT_TOKEN=7918946951:AAG... ✓
DATABASE_URL=postgresql://... ✓
```

#### Database Connection Problems
```bash
# Railway provides DATABASE_URL automatically
# Check Railway dashboard > Variables tab
# Ensure DATABASE_URL is present and valid
```

### Debug Mode
Enable detailed logging:
```env
LOG_LEVEL=DEBUG
```

### Health Check Endpoints
```bash
# Basic health
curl https://your-app.railway.app/health

# Detailed system info
curl https://your-app.railway.app/health/detailed

# Profile system status
curl https://your-app.railway.app/api/profiles/health
```

## Migration from Basic Memora

### Automatic Migration
If you're upgrading from basic Memora:
1. **No data loss** - All existing users and content preserved
2. **Auto-profile creation** - Profiles created for existing users on first interaction
3. **Backward compatibility** - All existing API endpoints continue working
4. **Gradual enhancement** - New features available immediately

### Manual Migration Check
```bash
# Check if migration is needed
curl https://your-app.railway.app/health/detailed

# Look for migration status in response
```

## Cost Optimization

### Railway Pricing Tiers
- **Hobby Plan**: $5/month - Perfect for personal use
- **Pro Plan**: $20/month - Ideal for teams and higher usage
- **Team Plan**: $20/month + usage - Best for production deployments

### Resource Optimization
- **Efficient Docker image** (~500MB compressed)
- **Smart dependency management** (only required packages)
- **Database connection pooling** (prevents connection exhaustion)
- **Async processing** (handles concurrent requests efficiently)

## Support & Updates

### Getting Help
1. **Check Railway logs** for error messages
2. **Use health endpoints** to diagnose issues
3. **Review environment variables** for missing configuration
4. **Check GitHub issues** for known problems

### Staying Updated
- **Auto-deployment** from GitHub when you push changes
- **Database migrations** run automatically
- **Backward compatibility** maintained across updates
- **Feature flags** for gradual rollouts

---

## Quick Links

- 🚀 **[Deploy to Railway](https://railway.app/template/memora-with-profiles)**
- 📚 **[API Documentation](USER_PROFILE_README.md)**
- 🤖 **[Telegram Bot Setup](https://t.me/botfather)**
- 🔑 **[OpenAI API Keys](https://platform.openai.com/api-keys)**
- 📊 **[Railway Dashboard](https://railway.app/dashboard)**

---

*Last updated: January 2025 - Memora with Enhanced User Profiles* 