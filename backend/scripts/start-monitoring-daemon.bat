@echo off
echo 🔍 Starting Website Monitoring Daemon...

rem Change to the backend directory
cd /d "%~dp0\.."

rem Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call .venv\Scripts\activate.bat
)

rem Set environment variables
set "PYTHONPATH=%PYTHONPATH%;%cd%\app"

rem Start the adaptive daemon (automatically chooses best mode)
python -m app.logic.adaptive_monitoring_daemon
