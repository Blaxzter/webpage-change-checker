# app/logic/background_service.py
import asyncio
import signal
import sys
from typing import Optional

from app.logic.website_checker import WebsiteMonitorService


class BackgroundTaskManager:
    """Manager for background services."""

    def __init__(self):
        self.monitor_service: Optional[WebsiteMonitorService] = None
        self.running = False

    async def start_services(self):
        """Start all background services."""
        print("Starting background services...")

        self.running = True

        # Start website monitoring service
        self.monitor_service = WebsiteMonitorService(check_interval_seconds=60)

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        try:
            # Run the monitoring service
            await self.monitor_service.start()
        except KeyboardInterrupt:
            print("Received shutdown signal")
        finally:
            await self.stop_services()

    async def stop_services(self):
        """Stop all background services gracefully."""
        print("Stopping background services...")

        self.running = False

        if self.monitor_service:
            await self.monitor_service.stop()
            self.monitor_service = None

        print("Background services stopped")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            print(f"Received signal {signum}")
            # Create a task to stop services
            loop = asyncio.get_event_loop()
            loop.create_task(self.stop_services())

        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point for background services."""
    manager = BackgroundTaskManager()
    await manager.start_services()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Service interrupted")
    except Exception as e:
        print(f"Service error: {e}")
        sys.exit(1)
