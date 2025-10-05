# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Memora** is an AI-powered personal memory assistant that helps users save, organize, and retrieve online content using natural language. The project consists of:

- **Frontend**: React Native mobile app (Expo) located in `MemoraTest/`
- **Backend**: FastAPI Python server located in `../app/`

The app enables users to save content from URLs, social media, files, and plain text, then search through their saved memories using semantic search powered by OpenAI embeddings.

## Repository Structure

```
memo/
├── MemoraTest/              # React Native frontend (current directory)
│   ├── src/
│   │   ├── components/      # Reusable UI components (Logo, LoadingScreen)
│   │   ├── config/          # Configuration (theme, Google OAuth)
│   │   ├── contexts/        # React contexts (AuthContext, ThemeContext)
│   │   ├── screens/         # Main screens (LoginScreen, ChatScreen, BrowseScreen, ProfileScreen)
│   │   ├── services/        # API client and authentication services
│   │   └── utils/           # Utility functions (share handler)
│   ├── App.tsx              # App entry point with navigation setup
│   ├── app.json             # Expo configuration
│   └── package.json         # Dependencies
│
└── app/                     # FastAPI backend (../app from here)
    ├── api/                 # API route handlers
    ├── db/                  # Database models and migrations
    ├── models/              # Pydantic schemas
    ├── scrapers/            # Social media content scrapers
    ├── services/            # Business logic services
    ├── utils/               # Utilities (LLM, search, file processing)
    └── main.py              # FastAPI application entry point
```

## Common Development Commands

### Frontend (React Native)

```bash
# Start development server
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios

# Test deep linking
npm run test:deep-linking
```

### Backend (FastAPI)

```bash
# Run backend server (from ../app directory)
python -m app.main

# Or with uvicorn (preferred for development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Initialize database
python -m app.cli db-migrate --init

# Run CLI commands
python -m app.cli save <user_id> <url>
python -m app.cli search <user_id> <query>
```

### Build & Deployment

```bash
# Build development version (Android)
eas build --platform android --profile development

# Build for iOS
eas build --platform ios --profile development

# Production build
eas build --platform ios --profile production
eas build --platform android --profile production

# Submit to app stores
eas submit --platform ios
eas submit --platform android
```

## Architecture

### Frontend Architecture

**Tech Stack:**
- **Framework**: React Native with Expo SDK 54
- **Navigation**: React Navigation (Bottom Tabs)
- **State Management**: React Context API
- **Storage**: AsyncStorage for user persistence
- **Authentication**: Google OAuth (expo-auth-session + @react-native-google-signin)
- **HTTP Client**: Fetch API via centralized service

**Key Components:**

1. **Authentication Flow** (`src/contexts/AuthContext.tsx`)
   - Manages user sign-in/sign-out state
   - Supports device auth and Google OAuth
   - Detects Expo Go vs development build environment
   - Persists user data in AsyncStorage

2. **Main Screens**:
   - **LoginScreen**: Google OAuth login interface
   - **ChatScreen**: Primary interaction UI for saving and searching content
   - **BrowseScreen**: Tag-based content browsing with filtering
   - **ProfileScreen**: User settings and account management

3. **API Service** (`src/services/api.ts`)
   - Centralized API client for backend communication
   - Base URL: `https://memora-production-da39.up.railway.app`
   - Endpoints: `/search`, `/extract`, `/save-text`, `/upload-file`, `/intent`

4. **Share Integration** (`src/utils/shareHandler.ts`)
   - Handles deep links from other apps via `memora://` scheme
   - Parses shared URLs and text content
   - Integrates with ChatScreen for seamless saving

### Backend Architecture

**Tech Stack:**
- **Framework**: FastAPI
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy
- **AI/ML**: OpenAI API (GPT-4 for analysis, text-embedding-ada-002 for vectors)
- **Content Extraction**: BeautifulSoup, custom scrapers for social media
- **File Processing**: Pillow (images), PyPDF2, python-docx

**Key Modules:**

1. **Content Extraction** (`app/utils/extractor.py`)
   - Detects content type (social media vs general web)
   - Routes to appropriate scraper (TikTok, Instagram, YouTube, etc.)
   - Falls back to general web scraping for unknown URLs
   - Extracts metadata, thumbnails, and text content

2. **Scrapers** (`app/scrapers/`)
   - `social_scraper.py`: Generic social media scraping
   - `tiktok_enhanced.py`: TikTok-specific scraper with enhanced metadata
   - `web_scraper.py`: General website content extraction
   - Handles platform-specific URL patterns and API formats

3. **LLM Integration** (`app/utils/llm.py`)
   - Generates embeddings for semantic search
   - Analyzes content to extract titles, descriptions, and tags
   - Supports image analysis via GPT-4 Vision
   - Intent detection for user queries (search vs save)

4. **Search System** (`app/utils/search.py`)
   - Vector similarity search using cosine distance
   - Dynamic similarity thresholds based on query
   - Filtering by content_type, platform, media_type
   - Tag-based grouping and retrieval

5. **Database Models** (`app/db/database.py`)
   - **User**: User accounts
   - **Item**: Saved content with embeddings
   - Fields: url, title, description, tags, embedding, content_type, platform, media_type, file_path, content_text, content_json

### Data Flow

**Saving Content:**
```
User shares URL → Deep link opens app → ChatScreen pre-fills URL →
User sends → Frontend calls /extract → Backend scrapes content →
LLM analyzes → Generates embedding → Saves to DB → Returns item
```

**Searching Content:**
```
User types query → Frontend calls /search → Backend generates query embedding →
Computes similarity scores → Filters and ranks results → Returns top K items
```

## Google Authentication

The app uses **two different Google OAuth implementations**:

1. **Expo Go / Development**: `expo-auth-session` (browser-based OAuth flow)
   - Configuration: `src/config/expoGoogle.ts`
   - Service: `src/services/expoGoogleAuth.ts`

2. **Development Build / Production**: `@react-native-google-signin/google-signin` (native SDK)
   - Configuration: `src/config/google.ts`
   - Service: `src/services/googleAuth.ts`

**Setup Requirements:**
- Google Cloud Console OAuth 2.0 Client IDs (iOS, Android, Web)
- Bundle ID: `com.memora.assistant`
- GoogleService-Info.plist for iOS
- URL schemes configured in app.json

See `GOOGLE_AUTH_SETUP.md` for detailed setup instructions.

## Deep Linking & Sharing

The app supports sharing content from other apps using:

- **Custom URL Scheme**: `memora://share?url=...`
- **Android Intent Filters**: Handles `SEND` actions for text/URLs
- **iOS Share Extension**: Configured via `expo-share-extension` plugin

**Implementation:**
- Deep link handling in `App.tsx` via `expo-linking`
- Share data parsing in `src/utils/shareHandler.ts`
- Shared content pre-fills ChatScreen input

## Database Migrations

Backend migrations run **automatically on startup**:

1. User profiles migration (`app/db/migrations/add_user_profiles.py`)
2. Item fields migration (`app/db/migrations/add_item_fields.py`)

Manual migration:
```bash
python -m app.cli db-migrate --init
```

## Environment Variables

### Frontend
- No environment variables required (API URL is hardcoded for production)

### Backend
```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # or sqlite:///./memora.db
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # optional
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

## Testing

### Frontend Testing
1. Use Expo Go for quick iteration (limited Google OAuth)
2. Build development version for full features: `eas build --profile development`
3. Test deep linking: `npm run test:deep-linking`

### Backend Testing
1. Health check: `curl http://localhost:8001/health`
2. API docs: `http://localhost:8001/docs` (Swagger UI)
3. Test extraction: `python -m app.cli save user1 https://youtube.com/watch?v=...`

## Deployment

### Frontend
- **Platform**: EAS Build (Expo Application Services)
- **iOS**: Requires Apple Developer account, provisioning profiles
- **Android**: APK for testing, AAB for Play Store
- See `IOS_BUILD_GUIDE.md` and `DEVELOPMENT_BUILD_GUIDE.md`

### Backend
- **Platform**: Railway
- **Database**: Railway PostgreSQL addon
- **URL**: `https://memora-production-da39.up.railway.app`
- Auto-deploys from Git, runs migrations on startup
- See `RAILWAY_DEPLOYMENT.md`

## Important Notes

### Frontend Development
- **Expo Go limitations**: Google Sign-in requires development build
- **Navigation**: Tab navigator with three tabs (Browse, Chat, Profile)
- **Theme**: Centralized in `src/config/theme.tsx`, accessed via `ThemeContext`
- **API errors**: Check backend logs at Railway dashboard

### Backend Development
- **Social media scrapers**: TikTok and Instagram may require updates as platforms change
- **Embedding costs**: OpenAI charges per token for embeddings
- **Database pooling**: Configured for Railway's connection limits
- **File uploads**: Stored in `/app/data` directory (configure Railway volumes for persistence)

### Common Issues

1. **Google Auth 404 Error**: Verify redirect URIs match exactly in Google Cloud Console
2. **Backend connection timeout**: Increase `DB_POOL_TIMEOUT` or check Railway logs
3. **Share extension not appearing**: Requires development build, not Expo Go
4. **Build failures**: Ensure icons are PNG (not SVG) in `assets/` directory

## Code Conventions

- **Frontend**: TypeScript with strict mode, functional components with hooks
- **Backend**: Python 3.9+, type hints preferred, PEP 8 style
- **Logging**: Use `logger.info()` liberally for debugging production issues
- **Error handling**: Always return descriptive error messages to frontend
