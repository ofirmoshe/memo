"""
Database migration script for Memora.

This script updates the database schema to add content_type and platform columns to the items table.
It should be run once after updating the code.
"""
import logging
import os
import sqlite3
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./memora.db")

def migrate_sqlite_db():
    """
    Migrate SQLite database to add content_type and platform columns.
    """
    # Extract SQLite file path from DATABASE_URL
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL[10:]
    else:
        logger.error(f"Unsupported database URL: {DATABASE_URL}")
        return
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found: {db_path}")
        logger.info("No migration needed. Database will be created with the new schema.")
        return
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Add content_type column if it doesn't exist
        if "content_type" not in column_names:
            logger.info("Adding content_type column to items table...")
            cursor.execute("ALTER TABLE items ADD COLUMN content_type TEXT")
            # Create index for content_type
            cursor.execute("CREATE INDEX ix_items_content_type ON items (content_type)")
            logger.info("content_type column added successfully.")
        else:
            logger.info("content_type column already exists.")
        
        # Add platform column if it doesn't exist
        if "platform" not in column_names:
            logger.info("Adding platform column to items table...")
            cursor.execute("ALTER TABLE items ADD COLUMN platform TEXT")
            # Create index for platform
            cursor.execute("CREATE INDEX ix_items_platform ON items (platform)")
            logger.info("platform column added successfully.")
        else:
            logger.info("platform column already exists.")
        
        # Commit changes
        conn.commit()
        logger.info("Database migration completed successfully.")
    
    except Exception as e:
        logger.error(f"Error migrating database: {str(e)}")
        raise
    finally:
        # Close connection
        if 'conn' in locals():
            conn.close()

def migrate_sqlalchemy_db():
    """
    Migrate database using SQLAlchemy.
    This is a more generic approach but may not work for all databases.
    """
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Add content_type column
        with engine.connect() as conn:
            # Check if content_type column exists
            if "sqlite" in DATABASE_URL:
                result = conn.execute(text("PRAGMA table_info(items)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                # Add columns if they don't exist
                if "content_type" not in column_names:
                    conn.execute(text("ALTER TABLE items ADD COLUMN content_type TEXT"))
                    # Create index
                    conn.execute(text("CREATE INDEX ix_items_content_type ON items (content_type)"))
                
                if "platform" not in column_names:
                    conn.execute(text("ALTER TABLE items ADD COLUMN platform TEXT"))
                    # Create index
                    conn.execute(text("CREATE INDEX ix_items_platform ON items (platform)"))
            
            # For PostgreSQL, MySQL, etc.
            else:
                # These may need to be adjusted based on the database
                try:
                    conn.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS content_type TEXT"))
                    conn.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS platform TEXT"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_items_content_type ON items (content_type)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_items_platform ON items (platform)"))
                except Exception as e:
                    logger.warning(f"Failed to add columns using database-agnostic approach: {str(e)}")
                    logger.warning("You may need to manually add the content_type and platform columns to your database.")
            
            conn.commit()
        
        logger.info("Database migration completed successfully.")
    
    except Exception as e:
        logger.error(f"Error migrating database: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting database migration...")
    
    # Choose migration method based on database type
    if DATABASE_URL.startswith("sqlite:///"):
        migrate_sqlite_db()
    else:
        migrate_sqlalchemy_db()
    
    logger.info("Migration process completed.") 