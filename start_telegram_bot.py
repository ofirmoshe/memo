#!/usr/bin/env python3
import time
import sys
import subprocess
import requests

def wait_for_backend():
    """Wait for the backend to be ready before starting the bot"""
    backend_url = "http://memora:8001/health"
    max_attempts = 30  # 5 minutes max
    attempt = 0
    
    print("Waiting for backend to be ready...")
    
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