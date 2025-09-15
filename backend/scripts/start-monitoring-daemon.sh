#!/bin/bash

# Start the website monitoring daemon as a separate process
# This avoids uvicorn + Playwright conflicts

echo "🔍 Starting Website Monitoring Daemon..."

# Change to the backend directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/app"

# Start the adaptive daemon (automatically chooses best mode)
python -m app.logic.adaptive_monitoring_daemon
