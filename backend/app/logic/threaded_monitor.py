# app/logic/threaded_monitor.py
"""
Thread-based monitoring service that runs in its own thread with its own event loop.
This avoids the uvicorn event loop conflicts while keeping it integrated with FastAPI.
"""
import asyncio
import threading
import sys
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from app.logic.website_checker import WebsiteMonitorService


class ThreadedMonitorService:
    """Monitoring service that runs in a separate thread."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.monitor_service: Optional[WebsiteMonitorService] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False

    def start(self):
        """Start the monitoring service in a separate thread."""
        if self.running:
            print("⚠️  Monitoring service is already running")
            return

        print("🚀 Starting threaded website monitoring service...")

        self.running = True
        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()

        print("✅ Threaded monitoring service started")

    def stop(self):
        """Stop the monitoring service."""
        if not self.running:
            return

        print("🛑 Stopping threaded monitoring service...")

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

        print("✅ Threaded monitoring service stopped")

    def _run_in_thread(self):
        """Run the monitoring service in a separate thread with its own event loop."""
        # Create a new event loop for this thread
        if sys.platform == "win32":
            # Use SelectorEventLoop on Windows for psycopg and Playwright compatibility
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            loop = asyncio.new_event_loop()
        else:
            loop = asyncio.new_event_loop()
            
        asyncio.set_event_loop(loop)
        self.loop = loop

        try:
            # Create and start the monitoring service
            self.monitor_service = WebsiteMonitorService(
                check_interval_seconds=self.check_interval_seconds
            )

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


# Global instance for use in FastAPI
threaded_monitor_service = ThreadedMonitorService()
