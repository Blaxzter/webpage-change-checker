import uuid
from abc import ABC
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Base(SQLModel, ABC):
    """Abstract base model for all SQLModel models in the application."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique identifier for the record",
        index=True,
    )

    # Let SQLModel handle the column creation automatically
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this record was created",
        # SQLModel will create the column automatically
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this record was last updated",
        # You'll need to handle updates in your application logic
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        class_name = self.__class__.__name__
        if self.id:
            return f"<{class_name}(id={self.id})>"
        return f"<{class_name}(new)>"


class SoftDeleteBase(Base):
    """Base model with soft delete functionality."""

    deleted_at: Optional[datetime] = Field(
        default=None,
        description="When this record was deleted (null if not deleted)",
    )

    is_deleted: bool = Field(
        default=False, description="Whether this record has been soft deleted"
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
