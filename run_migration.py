#!/usr/bin/env python3
"""
Migration Runner for Memora User Profiles
Safely applies database migrations for the user profile extension.
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.migrations.add_user_profiles import run_migration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables."""
    # Check for explicit DATABASE_URL (Railway, Heroku, etc.)
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Build from individual components
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "memora")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    else:
        return f"postgresql://{user}@{host}:{port}/{name}"

def create_backup_reminder():
    """Remind about backing up the database."""
    print("=" * 60)
    print("⚠️  IMPORTANT: DATABASE BACKUP REMINDER")
    print("=" * 60)
    print("Before running this migration, ensure you have:")
    print("1. A recent backup of your PostgreSQL database")
    print("2. Verified the backup can be restored")
    print("3. Scheduled maintenance window if needed")
    print()
    print("For PostgreSQL backup:")
    print("  pg_dump -h <host> -U <user> -d <database> > backup.sql")
    print()
    print("This migration is designed to be safe and preserve all data,")
    print("but a backup is always recommended for production systems.")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Run Memora user profile migration")
    parser.add_argument(
        "action", 
        choices=["apply", "rollback", "validate", "check"],
        help="Migration action to perform"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Skip confirmation prompts (USE WITH CAUTION)"
    )
    parser.add_argument(
        "--no-backup-reminder", 
        action="store_true",
        help="Skip backup reminder"
    )
    
    args = parser.parse_args()
    
    # Show backup reminder for destructive operations
    if args.action in ["apply", "rollback"] and not args.no_backup_reminder:
        create_backup_reminder()
        if not args.force:
            response = input("Have you created a backup? (yes/no): ").lower().strip()
            if response not in ["yes", "y"]:
                print("Please create a backup before proceeding.")
                sys.exit(1)
    
    # Get database URL
    try:
        database_url = get_database_url()
        logger.info("Connecting to database...")
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            logger.info("Database connection successful")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)
    
    # Run migration based on action
    try:
        if args.action == "check":
            from app.db.migrations.add_user_profiles import check_migration_needed
            needed = check_migration_needed(engine)
            if needed:
                print("✅ Migration is needed - user profile tables do not exist")
                sys.exit(0)
            else:
                print("ℹ️  Migration not needed - user profile tables already exist")
                sys.exit(0)
        
        elif args.action == "apply":
            if not args.force:
                print(f"\nAbout to apply user profile migration to database.")
                print("This will:")
                print("- Create user_profiles, user_auth_providers, and user_activity tables")
                print("- Add indexes and constraints")
                print("- Populate profiles for existing users")
                print("- Preserve all existing data")
                
                response = input("\nProceed with migration? (yes/no): ").lower().strip()
                if response not in ["yes", "y"]:
                    print("Migration cancelled.")
                    sys.exit(0)
            
            logger.info("Starting migration...")
            success = run_migration(engine, "apply")
            
            if success:
                logger.info("✅ Migration completed successfully!")
                print("\n🎉 User profile system is now active!")
                print("The Telegram bot and API can now use extended user profiles.")
            else:
                logger.error("❌ Migration failed!")
                sys.exit(1)
        
        elif args.action == "rollback":
            if not args.force:
                print("⚠️  WARNING: This will remove all user profile data!")
                print("This action:")
                print("- Drops user_profiles, user_auth_providers, and user_activity tables")
                print("- Removes all user profile information")
                print("- DOES NOT affect basic user records or saved content")
                
                response = input("\nAre you sure you want to rollback? (yes/no): ").lower().strip()
                if response not in ["yes", "y"]:
                    print("Rollback cancelled.")
                    sys.exit(0)
            
            logger.info("Starting rollback...")
            success = run_migration(engine, "rollback")
            
            if success:
                logger.info("✅ Rollback completed successfully!")
                print("User profile tables have been removed.")
            else:
                logger.error("❌ Rollback failed!")
                sys.exit(1)
        
        elif args.action == "validate":
            logger.info("Validating migration...")
            success = run_migration(engine, "validate")
            
            if success:
                logger.info("✅ Migration validation successful!")
                print("All user profile tables and constraints are properly configured.")
            else:
                logger.error("❌ Migration validation failed!")
                sys.exit(1)
    
    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        sys.exit(1)
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 