# app/schemas/website.py
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from datetime import datetime
import uuid
from typing import Any

from app.models.website import NotificationChannel, CheckStatus


class WebsiteBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Website display name"
    )
    url: HttpUrl = Field(..., description="Website URL to monitor")
    check_interval_minutes: int = Field(
        default=60,
        ge=1,
        le=10080,  # Max 1 week
        description="Check interval in minutes (1 min to 1 week)",
    )
    is_active: bool = Field(default=True, description="Whether monitoring is active")
    ignore_selectors: list[str] | None = Field(
        default=None, description="CSS selectors to ignore in change detection"
    )
    email_notifications: bool = Field(
        default=True, description="Send email notifications"
    )
    telegram_notifications: bool = Field(
        default=False, description="Send Telegram notifications"
    )

    @field_validator("ignore_selectors")
    def validate_selectors(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("Too many ignore selectors (max 50)")
        return v


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    check_interval_minutes: int | None = Field(None, ge=5, le=10080)
    is_active: bool | None = None
    ignore_selectors: list[str] | None = None
    email_notifications: bool | None = None
    telegram_notifications: bool | None = None


class WebsiteResponse(WebsiteBase):
    id: uuid.UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    # Convert URL back to string for response
    url: str

    class Config:
        from_attributes = True


class WebsiteListResponse(BaseModel):
    items: list[WebsiteResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Website Check Schemas
class WebsiteCheckBase(BaseModel):
    status: CheckStatus
    content_hash: str | None = None
    screenshot_path: str | None = None
    changes_detected: bool = False
    change_summary: str | None = None
    response_time_ms: int | None = Field(None, ge=0)
    error_message: str | None = None


class WebsiteCheckCreate(WebsiteCheckBase):
    website_id: uuid.UUID


class WebsiteCheckResponse(WebsiteCheckBase):
    id: uuid.UUID
    website_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class WebsiteCheckListResponse(BaseModel):
    items: list[WebsiteCheckResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Website with recent checks
class WebsiteWithChecks(WebsiteResponse):
    recent_checks: list[WebsiteCheckResponse] = Field(default_factory=list)
    last_check_at: datetime | None = None
    last_change_at: datetime | None = None


# Notification Settings Schemas
class NotificationSettingsBase(BaseModel):
    email_address: EmailStr | None = None
    email_enabled: bool = True
    telegram_chat_id: str | None = None
    telegram_enabled: bool = False
    telegram_bot_token: str | None = None


class NotificationSettingsCreate(NotificationSettingsBase):
    pass


class NotificationSettingsUpdate(BaseModel):
    email_address: EmailStr | None = None
    email_enabled: bool | None = None
    telegram_chat_id: str | None = None
    telegram_enabled: bool | None = None
    telegram_bot_token: str | None = None


class NotificationSettingsResponse(NotificationSettingsBase):
    id: uuid.UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Check trigger schema for manual checks
class CheckTrigger(BaseModel):
    website_ids: list[uuid.UUID] | None = Field(
        None,
        description="Specific website IDs to check, or None for all active websites",
    )


# Stats and dashboard schemas
class WebsiteStats(BaseModel):
    total_websites: int
    active_websites: int
    total_checks: int
    checks_last_24h: int
    websites_with_changes: int
    avg_response_time_ms: float | None


class DashboardResponse(BaseModel):
    stats: WebsiteStats
    recent_changes: list[WebsiteCheckResponse]
    failing_websites: list[WebsiteResponse]
