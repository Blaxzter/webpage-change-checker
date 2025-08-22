# Website Change Monitoring Service Startup Script for Windows
# PowerShell script to start the server with proper Playwright compatibility

param(
    [switch]$Hypercorn,
    [switch]$MonitoringEnabled,
    [string]$Host = "localhost",
    [int]$Port = 8000
)

Write-Host "🔍 Starting Webpage Change Monitoring Service..." -ForegroundColor Green

# Check if we're in the backend directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Error: Please run this script from the backend directory" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Error: Virtual environment not found. Please run 'uv sync' first" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Blue
& ".venv\Scripts\Activate.ps1"

# Check if Playwright browsers are installed
Write-Host "🎭 Checking Playwright installation..." -ForegroundColor Blue
try {
    python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()"
} catch {
    Write-Host "📥 Installing Playwright browsers..." -ForegroundColor Yellow
    playwright install chromium
}

# Create screenshots directory if it doesn't exist
if (-not (Test-Path "screenshots")) {
    Write-Host "📸 Creating screenshots directory..." -ForegroundColor Blue
    New-Item -ItemType Directory -Path "screenshots" -Force
}

# Set environment variables
if ($MonitoringEnabled) {
    $env:ENABLE_MONITORING = "true"
    Write-Host "✅ Website monitoring enabled" -ForegroundColor Green
} else {
    Write-Host "ℹ️ Website monitoring disabled (use -MonitoringEnabled to enable)" -ForegroundColor Yellow
}

if ($Hypercorn) {
    $env:USE_HYPERCORN = "true"
    Write-Host "🚀 Using hypercorn server (recommended for Windows + Playwright)" -ForegroundColor Green
} else {
    Write-Host "🚀 Using uvicorn server with fixed event loop" -ForegroundColor Green
}

# Start the server
Write-Host "📊 Server will be available at: http://${Host}:${Port}" -ForegroundColor Cyan
Write-Host "📚 API docs available at: http://${Host}:${Port}/docs" -ForegroundColor Cyan
Write-Host "🛑 Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

try {
    python -m app.main
} catch {
    Write-Host "❌ Server failed to start: $_" -ForegroundColor Red
    exit 1
}
