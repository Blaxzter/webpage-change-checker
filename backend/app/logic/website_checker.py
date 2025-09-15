# app/logic/website_checker.py
import asyncio
import hashlib
import json
import os
import traceback
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from difflib import unified_diff

from app.core.db import async_session
from app.crud.website import website, website_check
from app.models.website import Website, WebsiteCheck, CheckStatus
from app.schemas.website import WebsiteCheckCreate


class WebsiteChecker:
    """Service for checking websites for changes using Playwright."""

    def __init__(self, screenshots_dir: str = "screenshots"):
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.browser: Optional[Browser] = None

    async def start_browser(self):
        """Start the Playwright browser instance."""
        if self.browser is None:
            playwright = await async_playwright().start()

            # Windows-specific browser launch options to avoid subprocess issues
            import sys

            if sys.platform == "win32":
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding",
                        "--disable-extensions",
                        "--disable-plugins",
                        "--disable-default-apps",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-gpu",
                        "--single-process",  # This might help avoid subprocess issues
                    ],
                    # Try using a specific executable path if available
                    channel="chrome",  # Use system Chrome if available
                )
            else:
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                    ],
                )

    async def stop_browser(self):
        """Stop the Playwright browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None

    async def check_website(
        self, website_obj: Website, session: AsyncSession
    ) -> WebsiteCheckCreate:
        """
        Check a single website for changes.

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
            await self.start_browser()

            # Create new page
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            )
            page = await context.new_page()

            # Navigate to the website
            response = await page.goto(
                website_obj.url, wait_until="networkidle", timeout=30000
            )

            if not response or response.status >= 400:
                check_data.status = CheckStatus.FAILED
                check_data.error_message = (
                    f"HTTP {response.status if response else 'No response'}"
                )
                return check_data

            # Calculate response time
            end_time = datetime.now(datetime.timezone.utc)
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            check_data.response_time_ms = response_time_ms

            # Take screenshot
            screenshot_path = await self._take_screenshot(page, website_obj.id)
            check_data.screenshot_path = screenshot_path

            # Get page content
            content = await self._get_page_content(page, website_obj)
            content_hash = self._hash_content(content)
            check_data.content_hash = content_hash

            # Get previous check for comparison
            previous_check = await website_check.get_latest_for_website(
                session, website_id=str(website_obj.id)
            )

            # Compare with previous content
            if previous_check and previous_check.content_hash:
                if content_hash != previous_check.content_hash:
                    check_data.changes_detected = True
                    check_data.status = CheckStatus.CHANGED

                    # Generate change summary
                    change_summary = await self._generate_change_summary(
                        previous_check, content, website_obj
                    )
                    check_data.change_summary = change_summary
                else:
                    check_data.status = CheckStatus.SUCCESS
            else:
                # First check
                check_data.status = CheckStatus.SUCCESS
                check_data.change_summary = "Initial website check"

            await context.close()

        except PlaywrightTimeoutError:
            check_data.status = CheckStatus.FAILED
            check_data.error_message = "Page load timeout"
        except Exception as e:
            check_data.status = CheckStatus.FAILED
            check_data.error_message = str(e)

        return check_data

    async def _take_screenshot(self, page: Page, website_id: str) -> str:
        """Take a screenshot of the page."""
        timestamp = datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{website_id}_{timestamp}.png"
        filepath = self.screenshots_dir / filename

        await page.screenshot(path=str(filepath), full_page=True)
        return str(filepath)

    async def _get_page_content(self, page: Page, website_obj: Website) -> str:
        """Get page content excluding ignored selectors."""
        # Remove ignored elements
        if website_obj.ignore_selectors:
            try:
                ignore_list = json.loads(website_obj.ignore_selectors)
                for selector in ignore_list:
                    try:
                        await page.evaluate(
                            f"""
                            document.querySelectorAll("{selector}").forEach(el => el.remove())
                        """
                        )
                    except:
                        # Continue if selector fails
                        pass
            except (json.JSONDecodeError, TypeError):
                # Invalid JSON, continue without ignoring
                pass

        # Get cleaned content
        content = await page.evaluate(
            """
            () => {
                // Remove script and style elements
                const scripts = document.querySelectorAll('script, style, noscript');
                scripts.forEach(el => el.remove());
                
                // Get text content and normalize whitespace
                return document.body.innerText
                    .replace(/\\s+/g, ' ')
                    .trim();
            }
        """
        )

        return content

    def _hash_content(self, content: str) -> str:
        """Generate hash of content for comparison."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def _generate_change_summary(
        self, previous_check, current_content: str, website_obj: Website
    ) -> str:
        """Generate a summary of changes detected."""
        try:
            # For now, just return a basic summary
            # In future, could implement more sophisticated diff analysis
            return f"Changes detected at {datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            return "Changes detected"


class WebsiteMonitorService:
    """Background service for monitoring websites."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.checker = WebsiteChecker()
        self.running = False

    async def start(self):
        """Start the monitoring service."""
        self.running = True
        await self.checker.start_browser()

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
        self.running = False
        await self.checker.stop_browser()

    async def _check_due_websites(self):
        """Check websites that are due for monitoring."""
        async with async_session.begin() as session:
            try:
                # Get websites due for checking
                due_websites = await website.get_websites_due_for_check(session)

                if not due_websites:
                    return

                print(f"Checking {len(due_websites)} websites due for monitoring")

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
        print(f"Checking website: {website_obj.url}")

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


# Standalone functions for manual testing and API triggers
async def check_website_by_id(website_id: str) -> dict[str, Any]:
    """Check a specific website by ID."""
    async with async_session.begin() as session:
        website_obj = await website.get(session, id=website_id)
        if not website_obj:
            raise ValueError(f"Website {website_id} not found")

        checker = WebsiteChecker()
        try:
            check_result = await checker.check_website(website_obj, session)
            saved_check = await website_check.create(session, obj_in=check_result)
            return {
                "success": True,
                "check_id": str(saved_check.id),
                "changes_detected": check_result.changes_detected,
                "status": check_result.status,
            }
        finally:
            await checker.stop_browser()


async def check_websites_for_user(
    user_id: str, website_ids: list[str] | None = None
) -> dict[str, Any]:
    """Check websites for a specific user."""
    async with async_session.begin() as session:
        if website_ids:
            websites_to_check = []
            for website_id in website_ids:
                website_obj = await website.get_user_website(
                    session, website_id=website_id, user_id=user_id
                )
                if website_obj:
                    websites_to_check.append(website_obj)
        else:
            websites_to_check = await website.get_by_user(session, user_id=user_id)
            websites_to_check = [w for w in websites_to_check if w.is_active]

        checker = WebsiteChecker()
        results = []

        try:
            for website_obj in websites_to_check:
                check_result = await checker.check_website(website_obj, session)
                saved_check = await website_check.create(session, obj_in=check_result)
                results.append(
                    {
                        "website_id": str(website_obj.id),
                        "check_id": str(saved_check.id),
                        "changes_detected": check_result.changes_detected,
                        "status": check_result.status,
                    }
                )
        finally:
            await checker.stop_browser()

        return {"success": True, "checked_websites": len(results), "results": results}
