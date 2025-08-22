"""
SQLModel imports and base classes for the application.

This module provides the base SQLModel class and imports for database models.
"""

from sqlmodel import SQLModel

from .base import Base  # Import the Base model for common fields and functionality

# Import all your models here so they are registered with SQLModel
from .website import (
    Website,
    WebsiteCheck,
    NotificationLog,
    UserNotificationSettings,
    NotificationChannel,
    CheckStatus,
)

__all__ = [
    "SQLModel",
    "Base",
    "Website",
    "WebsiteCheck",
    "NotificationLog",
    "UserNotificationSettings",
    "NotificationChannel",
    "CheckStatus",
]
