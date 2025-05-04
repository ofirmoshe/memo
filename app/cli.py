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
def search(user_id: str, query: str, top_k: int):
    """Search saved content with a natural language query."""
    try:
        results = search_content(user_id=user_id, query=query, top_k=top_k)
        click.echo(f"Found {len(results)} results for query: '{query}'")
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
def db_migrate():
    """Run database migrations."""
    try:
        from app.db.migrate import migrate_sqlite_db, migrate_sqlalchemy_db
        import os
        
        # Determine database type
        database_url = os.getenv("DATABASE_URL", "sqlite:///./memora.db")
        
        click.echo("Starting database migration...")
        if database_url.startswith("sqlite:///"):
            migrate_sqlite_db()
        else:
            migrate_sqlalchemy_db()
        click.echo("Database migration completed.")
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli() 