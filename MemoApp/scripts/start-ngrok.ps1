# This script starts ngrok and automatically updates the URL in the config file
# Usage: .\scripts\start-ngrok.ps1 [port]
# Default port is 8000 if not specified

param (
    [int]$Port = 8000
)

# Check if ngrok is installed
try {
    $null = Get-Command ngrok -ErrorAction Stop
} catch {
    Write-Host "❌ Error: ngrok is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install it from https://ngrok.com/download"
    exit 1
}

Write-Host "🚀 Starting ngrok tunnel for port $Port..." -ForegroundColor Cyan

# Start ngrok in the background and capture its output
$logFile = "ngrok.log"
Start-Process -FilePath "ngrok" -ArgumentList "http $Port --log=stdout" -RedirectStandardOutput $logFile -NoNewWindow

# Wait for ngrok to start and get the URL
Write-Host "⏳ Waiting for ngrok to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Extract the public URL from ngrok's output
$content = Get-Content $logFile -ErrorAction SilentlyContinue
$ngrokUrl = $content | Select-String -Pattern "https://.*\.ngrok-free\.app" | ForEach-Object { $_.Matches[0].Value } | Select-Object -First 1

if (-not $ngrokUrl) {
    Write-Host "❌ Failed to get ngrok URL. Check ngrok.log for details." -ForegroundColor Red
    exit 1
}

Write-Host "✅ ngrok tunnel established: $ngrokUrl" -ForegroundColor Green

# Update the config file with the new URL
Write-Host "📝 Updating config.ts with the new ngrok URL..." -ForegroundColor Cyan
node scripts/update-ngrok-url.js $ngrokUrl

Write-Host "🔄 ngrok is running in a separate window. Press Ctrl+C in that window to stop." -ForegroundColor Cyan
Write-Host "📱 You can now run your Expo app and it will connect to the backend through ngrok." -ForegroundColor Green 