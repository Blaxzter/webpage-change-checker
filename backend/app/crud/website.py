# app/crud/website.py
from typing import Any, Sequence
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json
from datetime import datetime, timedelta

from app.crud.base import CRUDBase, NamedFilterFields
from app.models.website import (
    Website,
    WebsiteCheck,
    UserNotificationSettings,
    CheckStatus,
)
from app.schemas.website import (
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteCheckCreate,
    NotificationSettingsCreate,
    NotificationSettingsUpdate,
)


class CRUDWebsite(CRUDBase[Website, WebsiteCreate, WebsiteUpdate]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> Sequence[Website]:
        """Get websites for a specific user"""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(desc(self.model.created_at))
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_websites(self, db: AsyncSession) -> Sequence[Website]:
        """Get all active websites for monitoring"""
        query = select(self.model).where(self.model.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_websites_due_for_check(self, db: AsyncSession) -> Sequence[Website]:
        """Get websites that are due for checking based on their interval"""
        subquery = (
            select(
                WebsiteCheck.website_id,
                func.max(WebsiteCheck.created_at).label("last_check"),
            )
            .group_by(WebsiteCheck.website_id)
            .subquery()
        )

        query = (
            select(self.model)
            .outerjoin(subquery, self.model.id == subquery.c.website_id)
            .where(
                and_(
                    self.model.is_active == True,
                    or_(
                        # Never been checked
                        subquery.c.last_check.is_(None),
                        # Last check was more than interval ago
                        subquery.c.last_check
                        < func.now()
                        - func.make_interval(
                            0, 0, 0, 0, 0, self.model.check_interval_minutes
                        ),
                    ),
                )
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create_for_user(
        self, db: AsyncSession, *, obj_in: WebsiteCreate, user_id: str
    ) -> Website:
        """Create a website for a specific user"""
        # Convert ignore_selectors list to JSON string
        website_data = obj_in.model_dump()
        if website_data.get("ignore_selectors"):
            website_data["ignore_selectors"] = json.dumps(
                website_data["ignore_selectors"]
            )
        else:
            website_data["ignore_selectors"] = None

        website_data["user_id"] = user_id
        website_data["url"] = str(website_data["url"])  # Convert HttpUrl to string

        db_obj = self.model(**website_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_user_website(
        self, db: AsyncSession, *, website_id: str, user_id: str
    ) -> Website | None:
        """Get a specific website that belongs to a user"""
        query = select(self.model).where(
            and_(self.model.id == website_id, self.model.user_id == user_id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_with_recent_checks(
        self, db: AsyncSession, *, website_id: str, user_id: str, limit_checks: int = 10
    ) -> Website | None:
        """Get website with recent checks"""
        query = (
            select(self.model)
            .options(selectinload(self.model.checks).limit(limit_checks))
            .where(and_(self.model.id == website_id, self.model.user_id == user_id))
        )
        result = await db.execute(query)
        return result.scalars().first()


class CRUDWebsiteCheck(CRUDBase[WebsiteCheck, WebsiteCheckCreate, Any]):
    async def get_by_website(
        self, db: AsyncSession, *, website_id: str, skip: int = 0, limit: int = 100
    ) -> Sequence[WebsiteCheck]:
        """Get checks for a specific website"""
        query = (
            select(self.model)
            .where(self.model.website_id == website_id)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_recent_changes(
        self, db: AsyncSession, *, user_id: str | None = None, limit: int = 20
    ) -> Sequence[WebsiteCheck]:
        """Get recent changes across websites"""
        query = (
            select(self.model).join(Website).where(self.model.changes_detected == True)
        )

        if user_id:
            query = query.where(Website.user_id == user_id)

        query = query.order_by(desc(self.model.created_at)).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_failed_checks(
        self, db: AsyncSession, *, user_id: str | None = None, limit: int = 20
    ) -> Sequence[WebsiteCheck]:
        """Get recent failed checks"""
        query = (
            select(self.model)
            .join(Website)
            .where(self.model.status == CheckStatus.FAILED)
        )

        if user_id:
            query = query.where(Website.user_id == user_id)

        query = query.order_by(desc(self.model.created_at)).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_latest_for_website(
        self, db: AsyncSession, *, website_id: str
    ) -> WebsiteCheck | None:
        """Get the latest check for a website"""
        query = (
            select(self.model)
            .where(self.model.website_id == website_id)
            .order_by(desc(self.model.created_at))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_stats(
        self, db: AsyncSession, *, user_id: str | None = None, days: int = 30
    ) -> dict[str, Any]:
        """Get check statistics"""
        since_date = datetime.now(datetime.timezone.utc) - timedelta(days=days)

        base_query = select(self.model).join(Website)
        if user_id:
            base_query = base_query.where(Website.user_id == user_id)

        # Total checks
        total_checks_query = base_query.where(self.model.created_at >= since_date)
        total_checks = await db.scalar(
            select(func.count()).select_from(total_checks_query.subquery())
        )

        # Changes detected
        changes_query = base_query.where(
            and_(
                self.model.created_at >= since_date, self.model.changes_detected == True
            )
        )
        changes_count = await db.scalar(
            select(func.count()).select_from(changes_query.subquery())
        )

        # Failed checks
        failed_query = base_query.where(
            and_(
                self.model.created_at >= since_date,
                self.model.status == CheckStatus.FAILED,
            )
        )
        failed_count = await db.scalar(
            select(func.count()).select_from(failed_query.subquery())
        )

        # Average response time
        avg_response_query = base_query.where(
            and_(
                self.model.created_at >= since_date,
                self.model.response_time_ms.isnot(None),
            )
        )
        avg_response = await db.scalar(
            select(func.avg(self.model.response_time_ms)).select_from(
                avg_response_query.subquery()
            )
        )

        return {
            "total_checks": total_checks or 0,
            "changes_detected": changes_count or 0,
            "failed_checks": failed_count or 0,
            "avg_response_time_ms": float(avg_response) if avg_response else None,
            "success_rate": (
                ((total_checks - failed_count) / total_checks * 100)
                if total_checks > 0
                else 0
            ),
        }


class CRUDNotificationSettings(
    CRUDBase[
        UserNotificationSettings, NotificationSettingsCreate, NotificationSettingsUpdate
    ]
):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: str
    ) -> UserNotificationSettings | None:
        """Get notification settings for a user"""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def upsert_for_user(
        self,
        db: AsyncSession,
        *,
        obj_in: NotificationSettingsCreate | NotificationSettingsUpdate,
        user_id: str
    ) -> UserNotificationSettings:
        """Create or update notification settings for a user"""
        existing = await self.get_by_user(db, user_id=user_id)

        if existing:
            # Update existing
            update_data = obj_in.model_dump(exclude_unset=True)
            return await self.update(db, db_obj=existing, obj_in=update_data)
        else:
            # Create new
            settings_data = obj_in.model_dump()
            settings_data["user_id"] = user_id
            db_obj = self.model(**settings_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj


# Create instances
website = CRUDWebsite(Website)
website_check = CRUDWebsiteCheck(WebsiteCheck)
notification_settings = CRUDNotificationSettings(UserNotificationSettings)
