# app/models/website.py
from sqlmodel import Field, Relationship
from app.models.base import Base
import uuid
from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"


class CheckStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CHANGED = "changed"


class Website(Base, table=True):
    __tablename__ = "websites"

    name: str = Field(description="Website display name")
    url: str = Field(description="Website URL to monitor")
    check_interval_minutes: int = Field(
        default=60, description="Check interval in minutes"
    )
    is_active: bool = Field(default=True, description="Whether monitoring is active")

    # CSS selectors to ignore in diff
    ignore_selectors: str | None = Field(
        default=None, description="JSON array of CSS selectors to ignore"
    )

    # Notification settings
    email_notifications: bool = Field(
        default=True, description="Send email notifications"
    )
    telegram_notifications: bool = Field(
        default=False, description="Send Telegram notifications"
    )

    # User association
    user_id: str = Field(description="Auth0 user ID")

    # Relationships
    checks: list["WebsiteCheck"] = Relationship(
        back_populates="website", cascade_delete=True
    )


class WebsiteCheck(Base, table=True):
    __tablename__ = "website_checks"

    website_id: uuid.UUID = Field(
        foreign_key="websites.id", description="Associated website"
    )
    status: CheckStatus = Field(description="Check result status")

    # Check results
    content_hash: str | None = Field(default=None, description="Hash of page content")
    screenshot_path: str | None = Field(
        default=None, description="Path to screenshot file"
    )

    # Change detection
    changes_detected: bool = Field(
        default=False, description="Whether changes were detected"
    )
    change_summary: str | None = Field(
        default=None, description="Summary of changes detected"
    )

    # Performance metrics
    response_time_ms: int | None = Field(
        default=None, description="Page load time in milliseconds"
    )

    # Error details
    error_message: str | None = Field(
        default=None, description="Error message if check failed"
    )

    # Relationships
    website: Website = Relationship(back_populates="checks")


class NotificationLog(Base, table=True):
    __tablename__ = "notification_logs"

    website_check_id: uuid.UUID = Field(
        foreign_key="website_checks.id", description="Associated check"
    )
    channel: NotificationChannel = Field(description="Notification channel used")
    status: str = Field(description="Notification status (sent/failed)")
    recipient: str = Field(description="Email address or Telegram chat ID")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )


class UserNotificationSettings(Base, table=True):
    __tablename__ = "user_notification_settings"

    user_id: str = Field(description="Auth0 user ID", unique=True)

    # Email settings
    email_address: str | None = Field(
        default=None, description="Email address for notifications"
    )
    email_enabled: bool = Field(default=True, description="Email notifications enabled")

    # Telegram settings
    telegram_chat_id: str | None = Field(default=None, description="Telegram chat ID")
    telegram_enabled: bool = Field(
        default=False, description="Telegram notifications enabled"
    )
    telegram_bot_token: str | None = Field(
        default=None, description="Telegram bot token"
    )
