#!/usr/bin/env python
"""
Memora CLI - Command-line interface for Memora
"""
import click
import sys
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import Memora modules
from app.utils.extractor import extract_and_save_content
from app.utils.search import search_content
from app.db.database import init_db

@click.group()
def cli():
    """Memora - AI-powered Personal Memory Assistant."""
    # Initialize database
    init_db()

@cli.command()
@click.argument("user_id")
@click.argument("url")
def save(user_id: str, url: str):
    """Extract content from a URL and save it."""
    try:
        result = extract_and_save_content(user_id=user_id, url=url)
        click.echo(f"Content saved successfully!")
        click.echo(f"Title: {result['title']}")
        click.echo(f"Description: {result['description']}")
        click.echo(f"Tags: {', '.join(result['tags'])}")
        click.echo(f"ID: {result['id']}")
    except Exception as e:
        logger.error(f"Error saving content: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("user_id")
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of results to return", type=int)
@click.option("--threshold", "-t", default=0.0, help="Minimum similarity score threshold (0.0 to 1.0)", type=float)
@click.option("--content-type", "-c", default=None, help="Filter by content type", type=str)
@click.option("--platform", "-p", default=None, help="Filter by platform", type=str)
def search(user_id: str, query: str, top_k: int, threshold: float, content_type: str, platform: str):
    """Search saved content with a natural language query."""
    try:
        results = search_content(
            user_id=user_id, 
            query=query, 
            top_k=top_k,
            similarity_threshold=threshold,
            content_type=content_type,
            platform=platform
        )
        click.echo(f"Found {len(results)} results for query: '{query}'")
        if threshold > 0:
            click.echo(f"Using similarity threshold: {threshold}")
        click.echo("-" * 50)
        
        for i, result in enumerate(results):
            click.echo(f"{i+1}. {result['title']}")
            click.echo(f"   Score: {result['similarity_score']:.4f}")
            click.echo(f"   Description: {result['description'][:100]}...")
            click.echo(f"   Tags: {', '.join(result['tags'])}")
            click.echo(f"   URL: {result['url']}")
            click.echo("-" * 50)
    
    except Exception as e:
        logger.error(f"Error searching content: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def version():
    """Show version information."""
    click.echo("Memora v0.1.0")

@cli.command()
@click.option("--init", is_flag=True, help="Initialize Alembic if not already initialized")
def db_migrate(init: bool):
    """Run database migrations."""
    try:
        from app.db.migrate import migrate_database, initialize_alembic
        
        click.echo("Starting database migration...")
        
        # Initialize Alembic if requested
        if init:
            click.echo("Initializing Alembic...")
            if not initialize_alembic():
                click.echo("Failed to initialize Alembic", err=True)
                sys.exit(1)
            click.echo("Alembic initialized successfully.")
        
        # Run migrations
        if not migrate_database():
            click.echo("Database migration failed", err=True)
            sys.exit(1)
        
        click.echo("Database migration completed successfully.")
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("message", required=True)
def create_migration(message: str):
    """Create a new database migration."""
    try:
        import alembic.config
        
        click.echo(f"Creating new migration: {message}")
        
        # Create a new Alembic revision
        alembic_args = [
            '--raiseerr',
            'revision',
            '--autogenerate',
            '-m', message
        ]
        
        # Run the Alembic command
        alembic.config.main(argv=alembic_args)
        
        click.echo("Migration created successfully.")
    except Exception as e:
        logger.error(f"Error creating migration: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli() 