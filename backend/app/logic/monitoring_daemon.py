# app/logic/monitoring_daemon.py
"""
Standalone monitoring daemon that runs independently of FastAPI.
This avoids the uvicorn + Playwright event loop conflicts.
"""
import asyncio
import signal
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.logic.website_checker import WebsiteMonitorService


class MonitoringDaemon:
    def __init__(self):
        self.monitor_service = None
        self.running = False

    async def start(self):
        """Start the monitoring daemon."""
        print("🚀 Starting Website Monitoring Daemon...")

        self.running = True
        self.monitor_service = WebsiteMonitorService(check_interval_seconds=60)

        # Setup graceful shutdown handlers
        self._setup_signal_handlers()

        try:
            await self.monitor_service.start()
        except KeyboardInterrupt:
            print("📟 Received shutdown signal")
        except Exception as e:
            print(f"❌ Daemon error: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the monitoring daemon gracefully."""
        print("🛑 Stopping Website Monitoring Daemon...")

        self.running = False

        if self.monitor_service:
            await self.monitor_service.stop()
            self.monitor_service = None

        print("✅ Website Monitoring Daemon stopped")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            print(f"📡 Received signal {signum}")
            # Set the running flag to False to exit the main loop
            self.running = False

        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, "SIGTERM"):  # Windows doesn't have SIGTERM
            signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point for the monitoring daemon."""
    daemon = MonitoringDaemon()
    await daemon.start()


if __name__ == "__main__":
    # Set Windows event loop policy for psycopg and Playwright compatibility
    if sys.platform == "win32":
        # Use SelectorEventLoop which works with both psycopg and Playwright
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔄 Service interrupted by user")
    except Exception as e:
        print(f"💥 Service error: {e}")
        sys.exit(1)
