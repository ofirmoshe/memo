"""
Migration: Add User Profiles
Adds user_profiles, user_auth_providers, and user_activity tables.
Safe migration that preserves all existing data.
"""

import logging
from typing import Dict, Any
from sqlalchemy import text, MetaData, Table, Column, String, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.engine import Engine
from datetime import datetime

logger = logging.getLogger(__name__)

def get_migration_info() -> Dict[str, Any]:
    """Get migration metadata."""
    return {
        "version": "001",
        "name": "add_user_profiles",
        "description": "Add user profile tables with extended user information",
        "author": "memora",
        "created_at": "2024-01-01T00:00:00Z"
    }

def check_migration_needed(engine: Engine) -> bool:
    """Check if this migration needs to be applied."""
    try:
        with engine.connect() as conn:
            # Check if user_profiles table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_profiles'
                );
            """))
            exists = result.scalar()
            return not exists
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return True  # Assume migration is needed if we can't check

def apply_migration(engine: Engine) -> bool:
    """Apply the migration to add user profile tables."""
    try:
        with engine.begin() as conn:
            logger.info("Starting user profiles migration...")
            
            # 1. Create user_profiles table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id VARCHAR PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    display_name VARCHAR,
                    first_name VARCHAR,
                    last_name VARCHAR,
                    username VARCHAR,
                    email VARCHAR,
                    avatar_url VARCHAR,
                    country_code VARCHAR(2),
                    timezone VARCHAR,
                    primary_language VARCHAR(2) DEFAULT 'en',
                    secondary_languages JSON,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_active_at TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    is_verified BOOLEAN NOT NULL DEFAULT false,
                    is_premium BOOLEAN NOT NULL DEFAULT false,
                    preferences JSON,
                    total_items INTEGER NOT NULL DEFAULT 0,
                    total_searches INTEGER NOT NULL DEFAULT 0,
                    days_active INTEGER NOT NULL DEFAULT 0
                );
            """))
            
            # 2. Create indexes on user_profiles
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country_code);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_language ON user_profiles(primary_language);
            """))
            
            # 3. Create user_auth_providers table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_auth_providers (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    provider VARCHAR NOT NULL,
                    provider_user_id VARCHAR NOT NULL,
                    provider_username VARCHAR,
                    provider_email VARCHAR,
                    is_primary BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    provider_metadata JSON
                );
            """))
            
            # 4. Create indexes on user_auth_providers
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_auth_providers_user_id ON user_auth_providers(user_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_auth_providers_provider ON user_auth_providers(provider);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_auth_providers_provider_user_id ON user_auth_providers(provider_user_id);
            """))
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_user_auth_providers_unique ON user_auth_providers(user_id, provider);
            """))
            
            # 5. Create user_activity table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    activity_type VARCHAR NOT NULL,
                    activity_data JSON,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_agent VARCHAR,
                    ip_address VARCHAR,
                    source_platform VARCHAR,
                    source_version VARCHAR
                );
            """))
            
            # 6. Create indexes on user_activity
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_platform ON user_activity(source_platform);
            """))
            
            # 7. Create trigger to update updated_at on user_profiles
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            conn.execute(text("""
                DROP TRIGGER IF EXISTS trigger_user_profiles_updated_at ON user_profiles;
                CREATE TRIGGER trigger_user_profiles_updated_at
                    BEFORE UPDATE ON user_profiles
                    FOR EACH ROW
                    EXECUTE FUNCTION update_user_profiles_updated_at();
            """))
            
            # 8. Populate user_profiles for existing users
            logger.info("Populating user_profiles for existing users...")
            result = conn.execute(text("""
                INSERT INTO user_profiles (user_id, created_at, updated_at)
                SELECT id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                FROM users 
                WHERE id NOT IN (SELECT user_id FROM user_profiles)
                ON CONFLICT (user_id) DO NOTHING;
            """))
            
            rows_inserted = result.rowcount
            logger.info(f"Created profiles for {rows_inserted} existing users")
            
            # 9. Add Telegram auth providers for existing users
            logger.info("Adding Telegram auth providers for existing users...")
            conn.execute(text("""
                INSERT INTO user_auth_providers (user_id, provider, provider_user_id, is_primary, created_at)
                SELECT id, 'telegram', id, true, CURRENT_TIMESTAMP
                FROM users 
                WHERE id NOT IN (
                    SELECT user_id FROM user_auth_providers 
                    WHERE provider = 'telegram'
                )
                ON CONFLICT DO NOTHING;
            """))
            
            # 10. Update total_items count for existing users
            logger.info("Updating item counts for existing users...")
            conn.execute(text("""
                UPDATE user_profiles 
                SET total_items = (
                    SELECT COUNT(*) 
                    FROM items 
                    WHERE items.user_id = user_profiles.user_id
                )
                WHERE user_id IN (SELECT DISTINCT user_id FROM items);
            """))
            
            logger.info("User profiles migration completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error applying user profiles migration: {e}")
        raise

def rollback_migration(engine: Engine) -> bool:
    """Rollback the migration (remove user profile tables)."""
    try:
        with engine.begin() as conn:
            logger.info("Rolling back user profiles migration...")
            
            # Drop tables in reverse order (due to foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS user_activity CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS user_auth_providers CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS user_profiles CASCADE;"))
            
            # Drop the trigger function
            conn.execute(text("DROP FUNCTION IF EXISTS update_user_profiles_updated_at() CASCADE;"))
            
            logger.info("User profiles migration rollback completed!")
            return True
            
    except Exception as e:
        logger.error(f"Error rolling back user profiles migration: {e}")
        raise

def validate_migration(engine: Engine) -> bool:
    """Validate that the migration was applied correctly."""
    try:
        with engine.connect() as conn:
            # Check that all tables exist
            tables_to_check = ['user_profiles', 'user_auth_providers', 'user_activity']
            
            for table_name in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    );
                """))
                if not result.scalar():
                    logger.error(f"Table {table_name} was not created")
                    return False
            
            # Check that existing users have profiles
            result = conn.execute(text("""
                SELECT COUNT(*) FROM users 
                WHERE id NOT IN (SELECT user_id FROM user_profiles);
            """))
            missing_profiles = result.scalar()
            if missing_profiles > 0:
                logger.warning(f"{missing_profiles} users are missing profiles")
            
            # Check that constraints exist
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND table_name IN ('user_profiles', 'user_auth_providers', 'user_activity');
            """))
            foreign_keys = result.scalar()
            if foreign_keys < 3:  # Should have at least 3 foreign key constraints
                logger.warning("Some foreign key constraints may be missing")
            
            logger.info("Migration validation completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error validating migration: {e}")
        return False

# Migration runner function
def run_migration(engine: Engine, action: str = "apply") -> bool:
    """
    Run the migration with the specified action.
    
    Args:
        engine: SQLAlchemy engine
        action: 'apply', 'rollback', or 'validate'
    """
    migration_info = get_migration_info()
    logger.info(f"Running migration {migration_info['name']} (version {migration_info['version']})")
    
    if action == "apply":
        if not check_migration_needed(engine):
            logger.info("Migration already applied, skipping")
            return True
        return apply_migration(engine) and validate_migration(engine)
    
    elif action == "rollback":
        return rollback_migration(engine)
    
    elif action == "validate":
        return validate_migration(engine)
    
    else:
        logger.error(f"Unknown migration action: {action}")
        return False 