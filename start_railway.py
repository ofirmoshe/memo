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
        logger.info("⏳ Waiting 10 seconds for backend to fully initialize...")
        time.sleep(10)
        
        # Import and run the enhanced telegram bot with user profiles
        try:
            logger.info("🔍 Attempting to import enhanced Telegram bot...")
            from telegram_bot_enhanced import main as telegram_main
            logger.info("✅ Using enhanced Telegram bot with user profiles")
        except ImportError as e:
            logger.warning(f"⚠️ Enhanced bot not available ({e}), falling back to basic bot")
            try:
                from telegram_bot import main as telegram_main
                logger.info("✅ Using basic Telegram bot")
            except ImportError as e2:
                logger.error(f"❌ Could not import any Telegram bot: {e2}")
                raise
        
        logger.info("🚀 Starting Telegram bot main function...")
        telegram_main()
    except Exception as e:
        logger.error(f"❌ Failed to start Telegram bot: {e}")
        logger.exception("Full error traceback:")
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
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    logger.info(f"🔍 Environment check:")
    logger.info(f"  - TELEGRAM_BOT_TOKEN: {'✅ Set' if telegram_token else '❌ Missing'}")
    logger.info(f"  - OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")
    logger.info(f"  - DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '⚠️ Not set (will use SQLite)'}")
    logger.info(f"  - PORT: {os.getenv('PORT', '8001')}")
    
    missing_vars = []
    if not telegram_token:
        missing_vars.append("TELEGRAM_BOT_TOKEN")
    if not openai_key:
        missing_vars.append("OPENAI_API_KEY")
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Please set these variables in your Railway dashboard")
        sys.exit(1)
    
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