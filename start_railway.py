#!/usr/bin/env python3
"""
Railway deployment startup script.
Runs both the FastAPI backend and Telegram bot in the same process.
"""
import os
import sys
import time
import threading
import logging
import subprocess
import signal
from multiprocessing import Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def start_backend():
    """Start the FastAPI backend server."""
    logger.info("🚀 Starting FastAPI backend server...")
    try:
        import uvicorn
        # Use Railway's PORT environment variable, fallback to 8001
        port = int(os.getenv("PORT", "8001"))
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start backend: {e}")
        sys.exit(1)

def start_telegram_bot():
    """Start the Telegram bot."""
    logger.info("🤖 Starting Telegram bot...")
    try:
        # Wait a bit for the backend to start
        time.sleep(10)
        
        # Import and run the enhanced telegram bot with user profiles
        try:
            from telegram_bot_enhanced import main as telegram_main
            logger.info("Using enhanced Telegram bot with user profiles")
        except ImportError:
            logger.warning("Enhanced bot not available, falling back to basic bot")
            from telegram_bot import main as telegram_main
        
        telegram_main()
    except Exception as e:
        logger.error(f"❌ Failed to start Telegram bot: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("🛑 Received shutdown signal, stopping services...")
    sys.exit(0)

def main():
    """Main function to start both services."""
    logger.info("🚀 Starting Memora services for Railway deployment...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # DATABASE_URL is optional - if not provided, SQLite will be used
    if not os.getenv("DATABASE_URL"):
        logger.info("⚠️ DATABASE_URL not set, using SQLite database")
    
    logger.info("✅ All required environment variables are set")
    
    try:
        # Start backend in a separate process
        backend_process = Process(target=start_backend)
        backend_process.start()
        
        # Start telegram bot in a separate process
        bot_process = Process(target=start_telegram_bot)
        bot_process.start()
        
        # Wait for both processes
        backend_process.join()
        bot_process.join()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt, shutting down...")
        if 'backend_process' in locals():
            backend_process.terminate()
        if 'bot_process' in locals():
            bot_process.terminate()
    except Exception as e:
        logger.error(f"❌ Error in main process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 