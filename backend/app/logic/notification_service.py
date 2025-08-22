# app/logic/notification_service.py
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Optional
import httpx
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.website import notification_settings
from app.models.website import (
    Website,
    WebsiteCheck,
    UserNotificationSettings,
    NotificationChannel,
)
from app.schemas.website import WebsiteCheckCreate


class EmailNotificationService:
    """Service for sending email notifications."""

    def __init__(self):
        self.smtp_server = getattr(settings, "SMTP_SERVER", None)
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_username = getattr(settings, "SMTP_USERNAME", None)
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        self.from_email = getattr(settings, "FROM_EMAIL", self.smtp_username)

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return all(
            [self.smtp_server, self.smtp_username, self.smtp_password, self.from_email]
        )

    async def send_change_notification(
        self,
        website: Website,
        check: WebsiteCheck,
        user_settings: UserNotificationSettings,
    ) -> dict[str, Any]:
        """Send email notification about website changes."""

        if not self.is_configured():
            return {"success": False, "error": "Email service not configured"}

        if not user_settings.email_enabled or not user_settings.email_address:
            return {
                "success": False,
                "error": "Email notifications disabled or no email address",
            }

        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Website Change Detected: {website.name}"
            msg["From"] = self.from_email
            msg["To"] = user_settings.email_address

            # Create HTML and text versions
            html_content = self._create_html_email(website, check)
            text_content = self._create_text_email(website, check)

            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            await self._send_email(msg, user_settings.email_address)

            return {"success": True, "message": "Email sent successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_html_email(self, website: Website, check: WebsiteCheck) -> str:
        """Create HTML email content."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Website Change Detected</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; }}
                .website-name {{ font-size: 24px; margin: 0; }}
                .url {{ margin: 5px 0 0 0; opacity: 0.9; }}
                .content {{ margin: 20px 0; }}
                .detail {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #374151; }}
                .value {{ color: #6b7280; }}
                .changes {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
                .button {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 class="website-name">{website.name}</h1>
                    <p class="url">Changes detected on {website.url}</p>
                </div>
                
                <div class="content">
                    <div class="changes">
                        <h3>🔍 Changes Detected!</h3>
                        <p>We've detected changes on your monitored website.</p>
                        {f'<p><strong>Summary:</strong> {check.change_summary}</p>' if check.change_summary else ''}
                    </div>
                    
                    <div class="detail">
                        <span class="label">Check Time:</span>
                        <span class="value">{check.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
                    </div>
                    
                    {f'<div class="detail"><span class="label">Response Time:</span><span class="value">{check.response_time_ms}ms</span></div>' if check.response_time_ms else ''}
                    
                    <div class="detail">
                        <span class="label">Status:</span>
                        <span class="value">{check.status.value.title()}</span>
                    </div>
                    
                    <p>
                        <a href="{website.url}" class="button" target="_blank">View Website</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>This notification was sent because you have enabled email notifications for this website.</p>
                    <p>To manage your notification settings, please visit your dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_text_email(self, website: Website, check: WebsiteCheck) -> str:
        """Create plain text email content."""
        return f"""
Website Change Detected: {website.name}

Changes have been detected on your monitored website:
{website.url}

Details:
- Check Time: {check.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Status: {check.status.value.title()}
{f'- Response Time: {check.response_time_ms}ms' if check.response_time_ms else ''}
{f'- Summary: {check.change_summary}' if check.change_summary else ''}

To view the website: {website.url}

This notification was sent because you have enabled email notifications for this website.
To manage your notification settings, please visit your dashboard.
        """

    async def _send_email(self, msg: MIMEMultipart, to_email: str):
        """Send email using SMTP."""

        def _send_sync():
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_sync)


class TelegramNotificationService:
    """Service for sending Telegram notifications."""

    async def send_change_notification(
        self,
        website: Website,
        check: WebsiteCheck,
        user_settings: UserNotificationSettings,
    ) -> dict[str, Any]:
        """Send Telegram notification about website changes."""

        if (
            not user_settings.telegram_enabled
            or not user_settings.telegram_chat_id
            or not user_settings.telegram_bot_token
        ):
            return {
                "success": False,
                "error": "Telegram notifications disabled or incomplete settings",
            }

        try:
            message = self._create_telegram_message(website, check)

            # Send message via Telegram Bot API
            url = f"https://api.telegram.org/bot{user_settings.telegram_bot_token}/sendMessage"

            payload = {
                "chat_id": user_settings.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)

                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Telegram message sent successfully",
                    }
                else:
                    response_data = response.json()
                    return {
                        "success": False,
                        "error": f"Telegram API error: {response_data.get('description', 'Unknown error')}",
                    }

        except httpx.TimeoutException:
            return {"success": False, "error": "Telegram API timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_telegram_message(self, website: Website, check: WebsiteCheck) -> str:
        """Create Telegram message content."""
        message = f"""🔍 *Website Change Detected*

*{website.name}*
{website.url}

📅 *Check Time:* {check.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
📊 *Status:* {check.status.value.title()}
"""

        if check.response_time_ms:
            message += f"⏱️ *Response Time:* {check.response_time_ms}ms\n"

        if check.change_summary:
            message += f"📝 *Summary:* {check.change_summary}\n"

        message += f"\n[Visit Website]({website.url})"

        return message


class NotificationService:
    """Main notification service that coordinates all notification channels."""

    def __init__(self):
        self.email_service = EmailNotificationService()
        self.telegram_service = TelegramNotificationService()

    async def send_change_notification(
        self, website: Website, check: WebsiteCheck, session: AsyncSession
    ) -> dict[str, Any]:
        """Send notifications through all enabled channels for a website change."""

        # Get user notification settings
        user_settings = await notification_settings.get_by_user(
            session, user_id=website.user_id
        )

        if not user_settings:
            return {
                "success": False,
                "error": "No notification settings found for user",
            }

        results = {}

        # Send email notification if enabled
        if website.email_notifications and user_settings.email_enabled:
            email_result = await self.email_service.send_change_notification(
                website, check, user_settings
            )
            results["email"] = email_result

        # Send Telegram notification if enabled
        if website.telegram_notifications and user_settings.telegram_enabled:
            telegram_result = await self.telegram_service.send_change_notification(
                website, check, user_settings
            )
            results["telegram"] = telegram_result

        # Check if at least one notification was successful
        success = any(result.get("success", False) for result in results.values())

        return {
            "success": success,
            "results": results,
            "channels_attempted": len(results),
        }

    async def send_test_notification(
        self, user_id: str, channel: NotificationChannel, session: AsyncSession
    ) -> dict[str, Any]:
        """Send a test notification to verify settings."""

        user_settings = await notification_settings.get_by_user(
            session, user_id=user_id
        )

        if not user_settings:
            return {"success": False, "error": "No notification settings found"}

        # Create dummy website and check for testing
        test_website = Website(
            id="test-id",
            name="Test Website",
            url="https://example.com",
            user_id=user_id,
            email_notifications=True,
            telegram_notifications=True,
        )

        test_check = WebsiteCheck(
            id="test-check-id",
            website_id="test-id",
            status="changed",
            changes_detected=True,
            change_summary="This is a test notification",
            created_at=check.created_at if "check" in locals() else None,
        )

        if channel == NotificationChannel.EMAIL:
            return await self.email_service.send_change_notification(
                test_website, test_check, user_settings
            )
        elif channel == NotificationChannel.TELEGRAM:
            return await self.telegram_service.send_change_notification(
                test_website, test_check, user_settings
            )
        else:
            return {"success": False, "error": "Invalid notification channel"}


# Global notification service instance
notification_service = NotificationService()
