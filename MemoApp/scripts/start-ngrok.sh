#!/bin/bash

# This script starts ngrok and automatically updates the URL in the config file
# Usage: ./scripts/start-ngrok.sh [port]
# Default port is 8000 if not specified

# Default port
PORT=${1:-8000}

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok is not installed."
    echo "Please install it from https://ngrok.com/download"
    exit 1
fi

echo "🚀 Starting ngrok tunnel for port $PORT..."

# Start ngrok in the background and capture its output
ngrok http $PORT --log=stdout > ngrok.log &
NGROK_PID=$!

# Wait for ngrok to start and get the URL
echo "⏳ Waiting for ngrok to start..."
sleep 3

# Extract the public URL from ngrok's output
NGROK_URL=$(grep -o 'https://[^[:space:]]*\.ngrok-free.app' ngrok.log | head -n 1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL. Check ngrok.log for details."
    kill $NGROK_PID
    exit 1
fi

echo "✅ ngrok tunnel established: $NGROK_URL"

# Update the config file with the new URL
echo "📝 Updating config.ts with the new ngrok URL..."
node scripts/update-ngrok-url.js $NGROK_URL

# Keep ngrok running in the foreground
echo "🔄 ngrok is running... Press Ctrl+C to stop"
wait $NGROK_PID 