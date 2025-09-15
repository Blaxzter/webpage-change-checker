# app/logic/adaptive_threaded_monitor.py
"""
Adaptive thread-based monitoring service with automatic fallback.
This runs in a separate thread with its own event loop and automatically
falls back to HTTP-based monitoring if Playwright fails.
"""
import asyncio
import threading
import sys
import os
from typing import Optional

from app.logic.website_checker import WebsiteMonitorService
from app.logic.simple_website_checker import SimpleWebsiteMonitorService


class AdaptiveThreadedMonitorService:
    """Adaptive monitoring service that runs in a separate thread."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.monitor_service: Optional[
            WebsiteMonitorService | SimpleWebsiteMonitorService
        ] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        self.use_simple_mode = False

    def start(self):
        """Start the monitoring service in a separate thread."""
        if self.running:
            print("⚠️  Monitoring service is already running")
            return

        print("🚀 Starting adaptive threaded website monitoring service...")

        self.running = True
        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()

        print("✅ Adaptive threaded monitoring service started")

    def stop(self):
        """Stop the monitoring service."""
        if not self.running:
            return

        print("🛑 Stopping adaptive threaded monitoring service...")

        self.running = False

        # Stop the monitoring service in its own loop
        if self.loop and self.monitor_service:
            # Schedule the stop coroutine in the thread's event loop
            future = asyncio.run_coroutine_threadsafe(
                self.monitor_service.stop(), self.loop
            )
            try:
                future.result(timeout=10)  # Wait up to 10 seconds
            except Exception as e:
                print(f"⚠️  Error stopping monitor service: {e}")

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        print("✅ Adaptive threaded monitoring service stopped")

    def _run_in_thread(self):
        """Run the monitoring service in a separate thread with its own event loop."""
        # Create a new event loop for this thread
        if sys.platform == "win32":
            # Use SelectorEventLoop on Windows for psycopg compatibility
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop

        try:
            # Initialize the appropriate monitoring service
            loop.run_until_complete(self._initialize_monitoring_service())

            # Run the monitoring service
            loop.run_until_complete(self._run_monitoring())

        except Exception as e:
            print(f"❌ Error in monitoring thread: {e}")
        finally:
            # Clean up
            try:
                loop.close()
            except Exception as e:
                print(f"⚠️  Error closing event loop: {e}")

    async def _initialize_monitoring_service(self):
        """Initialize the appropriate monitoring service."""
        # First, check if we should use simple mode
        if self._should_use_simple_mode():
            print("🔄 Using Simple HTTP monitoring mode (threaded)")
            self.use_simple_mode = True
            self.monitor_service = SimpleWebsiteMonitorService(
                check_interval_seconds=self.check_interval_seconds
            )
            return

        # Try Playwright mode first
        try:
            print("🔍 Testing Playwright compatibility (threaded)...")
            await self._test_playwright_compatibility()
            print("✅ Playwright works, using full browser monitoring (threaded)")
            self.monitor_service = WebsiteMonitorService(
                check_interval_seconds=self.check_interval_seconds
            )
        except Exception as e:
            print(f"⚠️  Playwright test failed in thread: {e}")
            print("🔄 Falling back to Simple HTTP monitoring mode (threaded)")
            self.use_simple_mode = True
            self.monitor_service = SimpleWebsiteMonitorService(
                check_interval_seconds=self.check_interval_seconds
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
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process"],
            )
            await browser.close()
        finally:
            await playwright.stop()

    async def _run_monitoring(self):
        """Run the monitoring service with proper exception handling."""
        try:
            await self.monitor_service.start()
        except Exception as e:
            print(f"❌ Monitoring service error: {e}")
        finally:
            if self.monitor_service:
                try:
                    await self.monitor_service.stop()
                except Exception as e:
                    print(f"⚠️  Error stopping monitoring service: {e}")

    def get_status_info(self) -> dict:
        """Get detailed status information."""
        return {
            "running": self.running,
            "mode": "simple" if self.use_simple_mode else "playwright",
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "check_interval": self.check_interval_seconds,
        }


# Global instance for use in FastAPI
adaptive_threaded_monitor_service = AdaptiveThreadedMonitorService()

