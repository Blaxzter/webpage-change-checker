# app/logic/simple_website_checker.py
"""
Simple HTTP-based website monitoring that doesn't require Playwright.
This is a fallback option for Windows users experiencing subprocess issues.
"""
import asyncio
import hashlib
import json
import os
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import aiohttp
from bs4 import BeautifulSoup

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session
from app.crud.website import website, website_check
from app.models.website import Website, WebsiteCheck, CheckStatus
from app.schemas.website import WebsiteCheckCreate


class SimpleWebsiteChecker:
    """Simple HTTP-based website checker using aiohttp + BeautifulSoup."""

    def __init__(self, screenshots_dir: str = "screenshots"):
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None

    async def start_session(self):
        """Start the aiohttp session."""
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            )

    async def stop_session(self):
        """Stop the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def check_website(
        self, website_obj: Website, session: AsyncSession
    ) -> WebsiteCheckCreate:
        """
        Check a single website for changes using HTTP requests.

        Args:
            website_obj: Website model instance
            session: Database session

        Returns:
            WebsiteCheckCreate: Check result data
        """
        check_data = WebsiteCheckCreate(
            website_id=website_obj.id,
            status=CheckStatus.PENDING,
            changes_detected=False,
        )

        start_time = datetime.now(datetime.timezone.utc)

        try:
            await self.start_session()

            # Make HTTP request
            async with self.session.get(website_obj.url) as response:
                if response.status >= 400:
                    check_data.status = CheckStatus.FAILED
                    check_data.error_message = f"HTTP {response.status}"
                    return check_data

                # Calculate response time
                end_time = datetime.now(datetime.timezone.utc)
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                check_data.response_time_ms = response_time_ms

                # Get page content
                html_content = await response.text()
                content = self._extract_text_content(html_content, website_obj)
                content_hash = self._hash_content(content)
                check_data.content_hash = content_hash

                # Create a placeholder screenshot path
                check_data.screenshot_path = self._create_placeholder_screenshot(
                    website_obj.id
                )

                # Get previous check for comparison
                previous_check = await website_check.get_latest_for_website(
                    session, website_id=str(website_obj.id)
                )

                # Compare with previous content
                if previous_check and previous_check.content_hash:
                    if content_hash != previous_check.content_hash:
                        check_data.changes_detected = True
                        check_data.status = CheckStatus.CHANGED
                        check_data.change_summary = f"Content changes detected at {datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        check_data.status = CheckStatus.SUCCESS
                else:
                    # First check
                    check_data.status = CheckStatus.SUCCESS
                    check_data.change_summary = "Initial website check (HTTP-based)"

        except asyncio.TimeoutError:
            check_data.status = CheckStatus.FAILED
            check_data.error_message = "Request timeout"
        except aiohttp.ClientError as e:
            check_data.status = CheckStatus.FAILED
            check_data.error_message = f"HTTP error: {str(e)}"
        except Exception as e:
            check_data.status = CheckStatus.FAILED
            check_data.error_message = str(e)

        return check_data

    def _extract_text_content(self, html_content: str, website_obj: Website) -> str:
        """Extract text content from HTML using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()

            # Remove ignored selectors if specified
            if website_obj.ignore_selectors:
                try:
                    ignore_list = json.loads(website_obj.ignore_selectors)
                    for selector in ignore_list:
                        try:
                            for element in soup.select(selector):
                                element.decompose()
                        except Exception:
                            # Continue if selector fails
                            pass
                except (json.JSONDecodeError, TypeError):
                    # Invalid JSON, continue without ignoring
                    pass

            # Get text content and normalize whitespace
            text = soup.get_text()
            return " ".join(text.split())

        except Exception as e:
            print(f"Error extracting content: {e}")
            return html_content[:1000]  # Fallback to raw HTML snippet

    def _hash_content(self, content: str) -> str:
        """Generate hash of content for comparison."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _create_placeholder_screenshot(self, website_id: str) -> str:
        """Create a placeholder for screenshot since we can't take real screenshots."""
        timestamp = datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{website_id}_{timestamp}_placeholder.txt"
        filepath = self.screenshots_dir / filename

        # Create a simple text file as placeholder
        with open(filepath, "w") as f:
            f.write(
                f"HTTP-based monitoring - no screenshot available\nTimestamp: {timestamp}"
            )

        return str(filepath)


class SimpleWebsiteMonitorService:
    """Background service for monitoring websites using simple HTTP requests."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.checker = SimpleWebsiteChecker()
        self.running = False

    async def start(self):
        """Start the monitoring service."""
        print("🚀 Starting Simple HTTP Website Monitor...")
        self.running = True
        await self.checker.start_session()

        while self.running:
            try:
                await self._check_due_websites()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(self.check_interval_seconds)

    async def stop(self):
        """Stop the monitoring service."""
        print("🛑 Stopping Simple HTTP Website Monitor...")
        self.running = False
        await self.checker.stop_session()

    async def _check_due_websites(self):
        """Check websites that are due for monitoring."""
        async with async_session.begin() as session:
            try:
                # Get websites due for checking
                due_websites = await website.get_websites_due_for_check(session)

                if not due_websites:
                    return

                print(
                    f"Checking {len(due_websites)} websites due for monitoring (HTTP mode)"
                )

                # Check each website
                for website_obj in due_websites:
                    try:
                        await self._check_single_website(website_obj, session)
                    except Exception as e:
                        print(f"Error checking website {website_obj.url}: {e}")
                        # Log failed check
                        failed_check = WebsiteCheckCreate(
                            website_id=website_obj.id,
                            status=CheckStatus.FAILED,
                            error_message=str(e),
                        )
                        await website_check.create(session, obj_in=failed_check)

            except Exception as e:
                print(f"Error fetching due websites: {e}")

    async def _check_single_website(self, website_obj: Website, session: AsyncSession):
        """Check a single website and save results."""
        print(f"Checking website (HTTP): {website_obj.url}")

        # Perform the check
        check_result = await self.checker.check_website(website_obj, session)

        # Save check result
        await website_check.create(session, obj_in=check_result)

        # If changes detected, trigger notifications
        if check_result.changes_detected:
            print(f"Changes detected for {website_obj.url}")
            # TODO: Trigger notification service
            await self._trigger_notifications(website_obj, check_result)

    async def _trigger_notifications(
        self, website_obj: Website, check_result: WebsiteCheckCreate
    ):
        """Trigger notifications for detected changes."""
        from app.logic.notification_service import notification_service

        # Create a WebsiteCheck object for notification
        check_obj = WebsiteCheck(
            id=None,  # Will be set when saved
            website_id=website_obj.id,
            status=check_result.status,
            content_hash=check_result.content_hash,
            screenshot_path=check_result.screenshot_path,
            changes_detected=check_result.changes_detected,
            change_summary=check_result.change_summary,
            response_time_ms=check_result.response_time_ms,
            error_message=check_result.error_message,
            created_at=datetime.now(datetime.timezone.utc),
            updated_at=datetime.now(datetime.timezone.utc),
        )

        try:
            async with async_session.begin() as session:
                result = await notification_service.send_change_notification(
                    website_obj, check_obj, session
                )
                if result["success"]:
                    print(
                        f"Notifications sent for {website_obj.url}: {result['channels_attempted']} channels"
                    )
                else:
                    print(
                        f"Failed to send notifications for {website_obj.url}: {result.get('error', 'Unknown error')}"
                    )
        except Exception as e:
            print(f"Error sending notifications for {website_obj.url}: {e}")

