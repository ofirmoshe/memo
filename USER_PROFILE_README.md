# User Profile Extension for Memora

This document describes the comprehensive user profile system that extends Memora's basic user functionality with detailed profile information, multi-provider authentication, and advanced user analytics.

## 🎯 Overview

The user profile extension transforms Memora from a simple user ID-based system into a comprehensive user management platform that:

- **Preserves Backward Compatibility**: All existing users and data continue to work without migration
- **Supports Multiple Auth Providers**: Ready for Telegram, Google, Apple, and future authentication methods
- **Enables Rich User Profiles**: Name, preferences, location, language, and more
- **Provides Activity Tracking**: Comprehensive analytics for user behavior
- **Facilitates Mobile App Integration**: Full API support for future mobile applications

## 🏗️ Architecture

### Database Schema

```sql
-- Core extension tables
user_profiles         -- Extended profile information (1:1 with users)
user_auth_providers   -- Multiple authentication methods per user
user_activity        -- Activity tracking and analytics

-- Relationships
users (existing) -> user_profiles (new, 1:1)
users (existing) -> user_auth_providers (new, 1:many)
users (existing) -> user_activity (new, 1:many)
```

### Key Components

1. **Data Models** (`app/models/user_profile.py`)
   - Pydantic models for API requests/responses
   - Comprehensive enums for countries, languages, auth providers
   - Flexible user preferences system

2. **Database Models** (`app/db/user_profile_models.py`)
   - SQLAlchemy ORM models
   - Foreign key relationships to existing User table
   - JSON columns for flexible data storage

3. **Service Layer** (`app/services/user_profile_service.py`)
   - Business logic for profile management
   - Provider-specific user creation
   - Activity tracking and analytics

4. **API Endpoints** (`app/api/user_profile.py`)
   - RESTful API for profile operations
   - Batch operations for mobile app syncing
   - Provider-specific endpoints

5. **Migration System** (`app/db/migrations/add_user_profiles.py`)
   - Safe PostgreSQL migration
   - Automatic profile creation for existing users
   - Rollback capability

## 🚀 Getting Started

### 1. Run Migration

For **production with PostgreSQL**:

```bash
# Check if migration is needed
python run_migration.py check

# Apply migration (with backup reminder)
python run_migration.py apply

# Validate migration
python run_migration.py validate
```

For **development**:
```bash
# Auto-migration runs on first import
python -c "from app.db import init_database; init_database()"
```

### 2. Update Your Application

#### Option A: Use Enhanced Telegram Bot
```bash
# Replace telegram_bot.py with the enhanced version
cp telegram_bot_enhanced.py telegram_bot.py
```

#### Option B: Manual Integration
```python
from app.services.user_profile_service import UserProfileService
from app.models.user_profile import TelegramUserData

# Create user profile from Telegram data
telegram_data = TelegramUserData(
    telegram_user_id=user.id,
    first_name=user.first_name,
    last_name=user.last_name,
    username=user.username,
    language_code=user.language_code
)

with UserProfileService() as service:
    profile = service.create_from_telegram(telegram_data)
```

### 3. Add API Routes (Optional)

```python
from app.api.user_profile import router as user_profile_router

app.include_router(user_profile_router)
```

## 📊 Features

### 1. Rich User Profiles

```python
{
    "user_id": "123456789",
    "display_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "avatar_url": "https://...",
    "country_code": "US",
    "timezone": "America/New_York",
    "primary_language": "en",
    "secondary_languages": ["es", "fr"],
    "is_premium": false,
    "total_items": 42,
    "total_searches": 156,
    "last_active_at": "2024-01-15T10:30:00Z"
}
```

### 2. Multi-Provider Authentication

```python
# Telegram user
service.create_from_telegram(telegram_data)

# Google user (for future mobile app)
service.create_from_google(google_data)

# Apple user (for future mobile app)
service.create_from_apple(apple_data)
```

### 3. User Preferences

```python
{
    "default_language": "en",
    "auto_translate": true,
    "preferred_content_types": ["articles", "videos"],
    "search_suggestions": true,
    "ai_analysis_enabled": true,
    "auto_tagging": true,
    "daily_summary": false,
    "weekly_digest": true,
    "theme": "dark",
    "items_per_page": 20
}
```

### 4. Activity Tracking

```python
# Track any user activity
service.update_activity(
    user_id="123456789",
    activity_type="search",
    activity_data={"query": "python tutorials", "results_count": 5},
    source_platform="telegram"
)

# Get comprehensive stats
stats = service.get_user_stats(user_id)
```

## 🔧 API Usage

### Create Profile
```http
POST /api/v1/user/profile/telegram
Content-Type: application/json

{
    "telegram_user_id": 123456789,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "language_code": "en"
}
```

### Update Profile
```http
PUT /api/v1/user/profile/123456789
Content-Type: application/json

{
    "display_name": "John D.",
    "country_code": "CA",
    "timezone": "America/Toronto"
}
```

### Get Profile
```http
GET /api/v1/user/profile/123456789
```

### Update Preferences
```http
POST /api/v1/user/profile/123456789/preferences
Content-Type: application/json

{
    "theme": "dark",
    "auto_translate": true,
    "daily_summary": true
}
```

## 🛡️ Migration Safety

### Backward Compatibility Guarantees

1. **No Data Loss**: All existing users and content preserved
2. **API Compatibility**: Existing API endpoints continue to work
3. **Gradual Migration**: Profiles created on-demand for existing users
4. **Fallback Behavior**: System works even if profile creation fails

### Migration Process

1. **Pre-Migration**: Creates backup reminder and validation
2. **Schema Creation**: Adds new tables with proper constraints
3. **Data Population**: Creates profiles for all existing users
4. **Index Creation**: Optimizes database performance
5. **Validation**: Ensures migration completed successfully

### Rollback Capability

```bash
# If needed, rollback the migration
python run_migration.py rollback
```

## 📱 Mobile App Integration

The user profile system is designed for future mobile applications:

### Google Authentication Flow
```python
# Mobile app sends Google user data
google_data = GoogleUserData(
    google_user_id="google_123",
    email="user@gmail.com",
    name="John Doe",
    picture="https://..."
)

profile = service.create_from_google(google_data)
```

### Apple Authentication Flow
```python
# Mobile app sends Apple user data (limited by Apple's privacy)
apple_data = AppleUserData(
    apple_user_id="apple_123",
    email="user@privaterelay.appleid.com",  # May be hidden
    name="John Doe"
)

profile = service.create_from_apple(apple_data)
```

### Cross-Platform User Management
- Link multiple auth providers to single user account
- Sync preferences across platforms
- Unified content access regardless of sign-in method

## 🎛️ Configuration

### Environment Variables

```bash
# Database (PostgreSQL required for production)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Optional: Individual database components
DB_HOST=localhost
DB_PORT=5432
DB_NAME=memora
DB_USER=postgres
DB_PASSWORD=secret
```

### Service Configuration

```python
# UserProfileService supports dependency injection
class CustomUserProfileService(UserProfileService):
    def __init__(self, custom_db_session=None):
        self.db = custom_db_session or SessionLocal()
```

## 🔍 Monitoring & Analytics

### User Activity Types

- `start_command` - User started bot
- `message_received` - Any message received
- `search` - Search performed
- `search_results` - Search results returned
- `save_text` - Text content saved
- `save_url` - URL content saved
- `save_file` - File uploaded and processed
- `save_success` - Content saved successfully

### Available Statistics

```python
stats = service.get_user_stats(user_id)
# Returns: total_items, total_searches, days_active, last_active, created_at
```

### Database Queries for Analytics

```sql
-- Most active users
SELECT user_id, COUNT(*) as activities
FROM user_activity 
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY user_id 
ORDER BY activities DESC;

-- Popular content types
SELECT activity_data->>'content_type' as type, COUNT(*)
FROM user_activity 
WHERE activity_type = 'save_success'
GROUP BY activity_data->>'content_type';
```

## 🐛 Troubleshooting

### Common Issues

1. **Migration Fails**
   ```bash
   # Check database connectivity
   python run_migration.py check
   
   # Validate current state
   python run_migration.py validate
   ```

2. **Profile Service Errors**
   ```python
   # Enable debug logging
   import logging
   logging.getLogger('app.services.user_profile_service').setLevel(logging.DEBUG)
   ```

3. **API Errors**
   ```python
   # Check if user profile exists
   profile = service.get_profile(user_id)
   if not profile:
       # Create profile manually
       user, profile = service.get_or_create_user_with_profile(user_id)
   ```

### Performance Optimization

1. **Database Indexes**: All foreign keys and search columns are indexed
2. **Connection Pooling**: Use SQLAlchemy pool settings
3. **Batch Operations**: Use batch API endpoints for bulk updates
4. **Caching**: Consider Redis for frequently accessed profiles

## 🤝 Contributing

### Adding New Auth Providers

1. Add provider to `AuthProvider` enum
2. Create provider-specific data model
3. Implement `create_from_<provider>` method
4. Add API endpoint
5. Update migration if needed

### Extending User Preferences

1. Update `UserPreferences` model
2. Add validation logic
3. Update API documentation
4. Test backward compatibility

## 📚 Related Documentation

- [Original Memora Documentation](README.md)
- [API Documentation](docs/api.md)
- [Database Schema](docs/schema.md)
- [Migration Guide](docs/migration.md)

---

This user profile extension provides a solid foundation for scaling Memora from a simple Telegram bot to a comprehensive multi-platform memory assistant. The system is designed to grow with your needs while maintaining backward compatibility and data integrity. 