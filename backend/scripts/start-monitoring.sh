#!/bin/bash

# Website Change Monitoring Service Startup Script

set -e

echo "🔍 Starting Webpage Change Monitoring Service..."

# Check if we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ] && [ ! -f ".venv/bin/activate" ]; then
    echo "❌ Error: Virtual environment not found. Please run 'uv sync' first"
    exit 1
fi

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Playwright browsers are installed
echo "🎭 Checking Playwright installation..."
if ! python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()" 2>/dev/null; then
    echo "📥 Installing Playwright browsers..."
    playwright install chromium
fi

# Create screenshots directory if it doesn't exist
if [ ! -d "screenshots" ]; then
    echo "📸 Creating screenshots directory..."
    mkdir -p screenshots
    chmod 755 screenshots
fi

# Check database connection
echo "🗄️  Checking database connection..."
if ! python -c "
import asyncio
from app.core.db import get_db

async def check_db():
    try:
        async with get_db() as session:
            await session.execute('SELECT 1')
        print('✅ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

if not asyncio.run(check_db()):
    exit(1)
"; then
    exit 1
fi

echo "🚀 Starting monitoring service..."
echo "📊 Dashboard available at: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop"

# Start the background monitoring service
python -m app.logic.background_service
