@echo off
REM Website Change Monitoring Service Startup Script for Windows
REM Batch script to start the server with proper Playwright compatibility

echo 🔍 Starting Webpage Change Monitoring Service...

REM Check if we're in the backend directory
if not exist "pyproject.toml" (
    echo ❌ Error: Please run this script from the backend directory
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Error: Virtual environment not found. Please run 'uv sync' first
    exit /b 1
)

REM Activate virtual environment
echo 📦 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if Playwright browsers are installed
echo 🎭 Checking Playwright installation...
python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()" 2>nul
if errorlevel 1 (
    echo 📥 Installing Playwright browsers...
    playwright install chromium
)

REM Create screenshots directory if it doesn't exist
if not exist "screenshots" (
    echo 📸 Creating screenshots directory...
    mkdir screenshots
)

REM Set default environment variables (can be overridden)
if not defined ENABLE_MONITORING set ENABLE_MONITORING=false
if not defined USE_HYPERCORN set USE_HYPERCORN=false

echo 🚀 Starting server...
echo 📊 Server will be available at: http://localhost:8000
echo 📚 API docs available at: http://localhost:8000/docs
echo 🛑 Press Ctrl+C to stop
echo.

REM Start the server
python -m app.main

if errorlevel 1 (
    echo ❌ Server failed to start
    exit /b 1
)
