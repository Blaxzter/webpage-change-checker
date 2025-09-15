# app/logic/adaptive_monitoring_daemon.py
"""
Adaptive monitoring daemon that automatically falls back to HTTP-based monitoring
if Playwright fails on Windows. This provides maximum compatibility.
"""
import asyncio
import signal
import sys
import os
from pathlib import Path
from typing import Optional

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.logic.website_checker import WebsiteMonitorService
from app.logic.simple_website_checker import SimpleWebsiteMonitorService


class AdaptiveMonitoringDaemon:
    """
    Monitoring daemon that tries Playwright first, falls back to HTTP requests.
    """

    def __init__(self):
        self.monitor_service: Optional[
            WebsiteMonitorService | SimpleWebsiteMonitorService
        ] = None
        self.running = False
        self.use_simple_mode = False

    async def start(self):
        """Start the monitoring daemon with automatic fallback."""
        print("🚀 Starting Adaptive Website Monitoring Daemon...")

        self.running = True

        # Setup graceful shutdown handlers
        self._setup_signal_handlers()

        # Try to determine the best monitoring approach
        await self._initialize_monitoring_service()

        try:
            await self.monitor_service.start()
        except KeyboardInterrupt:
            print("📟 Received shutdown signal")
        except Exception as e:
            print(f"❌ Daemon error: {e}")
            raise
        finally:
            await self.stop()

    async def _initialize_monitoring_service(self):
        """Initialize the appropriate monitoring service."""
        # First, try to detect if we should use simple mode
        if self._should_use_simple_mode():
            print("🔄 Using Simple HTTP monitoring mode")
            self.use_simple_mode = True
            self.monitor_service = SimpleWebsiteMonitorService(
                check_interval_seconds=60
            )
            return

        # Try Playwright mode first
        try:
            print("🔍 Testing Playwright compatibility...")
            await self._test_playwright_compatibility()
            print("✅ Playwright works, using full browser monitoring")
            self.monitor_service = WebsiteMonitorService(check_interval_seconds=60)
        except Exception as e:
            print(f"⚠️  Playwright test failed: {e}")
            print("🔄 Falling back to Simple HTTP monitoring mode")
            self.use_simple_mode = True
            self.monitor_service = SimpleWebsiteMonitorService(
                check_interval_seconds=60
            )

    def _should_use_simple_mode(self) -> bool:
        """Check if we should use simple mode based on environment."""
        # Force simple mode if environment variable is set
        if os.getenv("USE_SIMPLE_MONITORING", "false").lower() == "true":
            return True

        # On Windows with Python 3.13+, prefer simple mode by default
        if sys.platform == "win32" and sys.version_info >= (3, 13):
            return True

        return False

    async def _test_playwright_compatibility(self):
        """Test if Playwright can start successfully."""
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        try:
            browser = await playwright.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            await browser.close()
        finally:
            await playwright.stop()

    async def stop(self):
        """Stop the monitoring daemon gracefully."""
        print("🛑 Stopping Adaptive Website Monitoring Daemon...")

        self.running = False

        if self.monitor_service:
            await self.monitor_service.stop()
            self.monitor_service = None

        print("✅ Adaptive Website Monitoring Daemon stopped")

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
    """Main entry point for the adaptive monitoring daemon."""
    daemon = AdaptiveMonitoringDaemon()
    await daemon.start()


if __name__ == "__main__":
    # Set Windows event loop policy for database compatibility
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔄 Service interrupted by user")
    except Exception as e:
        print(f"💥 Service error: {e}")
        sys.exit(1)

