"""
Database migration script for Memora.

This script handles database migrations using Alembic.
"""
import logging
import os
import subprocess
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import alembic.config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./memora.db")

def migrate_using_alembic():
    """
    Run database migrations using Alembic.
    """
    try:
        logger.info("Running Alembic migrations...")
        
        # Create a new Alembic config
        alembic_args = [
            '--raiseerr',
            'upgrade', 'head',
        ]
        
        try:
            # Run the Alembic command
            alembic.config.main(argv=alembic_args)
            logger.info("Alembic migrations completed successfully.")
            return True
        except Exception as e:
            logger.error(f"Error running Alembic migrations: {str(e)}")
            # Fall back to creating tables directly
            logger.info("Falling back to direct table creation...")
            from app.db.database import Base, engine
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created directly via SQLAlchemy.")
            return True
            
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        return False

def initialize_alembic():
    """
    Initialize Alembic if it hasn't been initialized yet.
    """
    try:
        # Check if versions directory exists
        versions_dir = os.path.join(os.getcwd(), 'alembic', 'versions')
        if not os.path.exists(versions_dir):
            os.makedirs(versions_dir, exist_ok=True)
        
        # Check if there are any migration files
        if len(os.listdir(versions_dir)) == 0:
            logger.info("No Alembic migrations found. Creating initial migration...")
            
            try:
                # Create a new Alembic revision
                alembic_args = [
                    '--raiseerr',
                    'revision',
                    '--autogenerate',
                    '-m', 'Initial migration'
                ]
                
                # Run the Alembic command
                alembic.config.main(argv=alembic_args)
                
                logger.info("Initial Alembic migration created.")
            except Exception as e:
                logger.error(f"Error creating initial migration: {str(e)}")
                # Fall back to creating tables directly
                logger.info("Falling back to direct table creation...")
                from app.db.database import Base, engine
                Base.metadata.create_all(bind=engine)
                logger.info("Tables created directly via SQLAlchemy.")
                return True
        
        return True
    except Exception as e:
        logger.error(f"Error initializing Alembic: {str(e)}")
        # Fall back to creating tables directly
        try:
            logger.info("Falling back to direct table creation...")
            from app.db.database import Base, engine
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created directly via SQLAlchemy.")
            return True
        except Exception as inner_e:
            logger.error(f"Error creating tables directly: {str(inner_e)}")
            return False

def migrate_sqlite_db():
    """
    Legacy migration for SQLite database.
    This is kept for backwards compatibility.
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
    
    logger.info("Using legacy migration for SQLite. Consider switching to Alembic for future migrations.")
    
    # Import SQLite module only if needed
    import sqlite3
    
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
            
        # Add new media-related columns
        new_columns = [
            ("media_type", "TEXT NOT NULL DEFAULT 'url'"),
            ("content_data", "TEXT"),
            ("file_path", "TEXT"),
            ("file_size", "INTEGER"),
            ("mime_type", "TEXT"),
            ("user_context", "TEXT")
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in column_names:
                logger.info(f"Adding {column_name} column to items table...")
                cursor.execute(f"ALTER TABLE items ADD COLUMN {column_name} {column_def}")
                if column_name == "media_type":
                    cursor.execute("CREATE INDEX ix_items_media_type ON items (media_type)")
                logger.info(f"{column_name} column added successfully.")
            else:
                logger.info(f"{column_name} column already exists.")
                
        # Make url column nullable for existing records
        cursor.execute("PRAGMA foreign_keys=off")
        cursor.execute("""
            CREATE TABLE items_new (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                url TEXT,
                title TEXT,
                description TEXT,
                tags TEXT,
                timestamp DATETIME,
                embedding TEXT,
                content_type TEXT,
                platform TEXT,
                media_type TEXT NOT NULL DEFAULT 'url',
                content_data TEXT,
                file_path TEXT,
                file_size INTEGER,
                mime_type TEXT,
                user_context TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            INSERT INTO items_new SELECT 
                id, user_id, url, title, description, tags, timestamp, embedding, 
                content_type, platform, 
                COALESCE(media_type, 'url'),
                content_data, file_path, file_size, mime_type, user_context
            FROM items
        """)
        cursor.execute("DROP TABLE items")
        cursor.execute("ALTER TABLE items_new RENAME TO items")
        cursor.execute("PRAGMA foreign_keys=on")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX ix_items_url ON items (url)")
        cursor.execute("CREATE INDEX ix_items_content_type ON items (content_type)")
        cursor.execute("CREATE INDEX ix_items_platform ON items (platform)")
        cursor.execute("CREATE INDEX ix_items_media_type ON items (media_type)")
        
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

def check_database_connection():
    """
    Check if the database is accessible.
    """
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Try to connect
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info(f"Successfully connected to database: {DATABASE_URL}")
        return True
    except OperationalError as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error connecting to database: {str(e)}")
        return False

def migrate_database():
    """
    Main migration function that orchestrates the migration process.
    """
    logger.info("Starting database migration process...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed. Migration aborted.")
        return False
    
    # For SQLite, use the legacy migration method
    if DATABASE_URL.startswith("sqlite:///"):
        migrate_sqlite_db()
        return True
    
    # For other databases, use Alembic
    # Initialize Alembic if needed
    if not initialize_alembic():
        logger.error("Failed to initialize Alembic. Migration aborted.")
        return False
    
    # Run migrations
    if not migrate_using_alembic():
        logger.error("Alembic migration failed.")
        return False
    
    logger.info("Database migration completed successfully.")
    return True

if __name__ == "__main__":
    success = migrate_database()
    if not success:
        sys.exit(1) 