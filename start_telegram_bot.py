#!/usr/bin/env python3
import time
import sys
import subprocess
import requests
import os

def get_backend_url():
    """Get the appropriate backend URL based on the environment."""
    # Check if we're running on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        # On Railway, use localhost since both services run in the same container
        return "http://localhost:" + os.getenv("PORT", "8001")
    
    # Check if BACKEND_URL is explicitly set (for other cloud providers or custom setups)
    if os.getenv("BACKEND_URL"):
        return os.getenv("BACKEND_URL")
    
    # Check if we're running in Docker (docker-compose)
    if os.getenv("DATABASE_URL") and "postgres" in os.getenv("DATABASE_URL", ""):
        return "http://memora:8001"  # Docker service name
    
    # Default to localhost for local development
    return "http://localhost:8001"

def wait_for_backend():
    """Wait for the backend to be ready before starting the bot"""
    backend_url = get_backend_url() + "/health"
    max_attempts = 30  # 5 minutes max
    attempt = 0
    
    print(f"Waiting for backend to be ready at: {backend_url}")
    
    while attempt < max_attempts:
        try:
            response = requests.get(backend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except Exception as e:
            print(f"⏳ Backend not ready yet (attempt {attempt + 1}/{max_attempts}): {e}")
        
        attempt += 1
        time.sleep(10)
    
    print("❌ Backend failed to become ready within timeout")
    return False

def start_bot():
    """Start the Telegram bot"""
    print("🚀 Starting Telegram bot...")
    try:
        subprocess.run([sys.executable, "telegram_bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if wait_for_backend():
        start_bot()
    else:
        sys.exit(1) 