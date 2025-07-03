"""
Database initialization with user profile extension.
Ensures all tables and relationships are properly set up.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .database import Base, engine, SessionLocal
from .user_profile_models import UserProfile, UserAuthProvider, UserActivity, extend_user_model

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all tables including user profiles."""
    try:
        logger.info("Initializing database with user profile extension...")
        
        # Extend the User model with relationships
        extend_user_model()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def check_user_profile_tables():
    """Check if user profile tables exist."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        required_tables = ['user_profiles', 'user_auth_providers', 'user_activity']
        existing_tables = inspector.get_table_names()
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"Missing user profile tables: {missing_tables}")
            return False
        
        logger.info("All user profile tables exist")
        return True
        
    except Exception as e:
        logger.error(f"Error checking user profile tables: {e}")
        return False

def run_user_profile_migration():
    """Run user profile migration if needed."""
    try:
        if check_user_profile_tables():
            logger.info("User profile tables already exist, skipping migration")
            return True
        
        logger.info("Running user profile migration...")
        from .migrations.add_user_profiles import run_migration
        
        success = run_migration(engine, "apply")
        if success:
            logger.info("User profile migration completed successfully")
        else:
            logger.error("User profile migration failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Error running user profile migration: {e}")
        return False

# Auto-initialize on import
try:
    init_database()
    
    # Check if migration is needed and run it
    if not check_user_profile_tables():
        logger.info("User profile tables not found, attempting auto-migration...")
        run_user_profile_migration()
        
except Exception as e:
    logger.warning(f"Auto-initialization failed: {e}")
    logger.info("Manual migration may be required using run_migration.py") 