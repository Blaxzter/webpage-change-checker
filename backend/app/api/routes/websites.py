# app/api/routes/websites.py
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.api.deps import DBDep, auth0
from app.crud.website import website, website_check, notification_settings
from app.schemas.website import (
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteResponse,
    WebsiteListResponse,
    WebsiteWithChecks,
    WebsiteCheckListResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    CheckTrigger,
    DashboardResponse,
    WebsiteStats,
)
from app.models.website import NotificationChannel


router = APIRouter(prefix="/websites", tags=["websites"])


@router.get("/", response_model=WebsiteListResponse)
async def get_websites(
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """Get user's websites with pagination."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    websites = await website.get_by_user(
        session, user_id=user_id, skip=skip, limit=limit
    )

    # Get total count for pagination
    total = await website.get_count(
        session, filter_by=[("user_id", user_id, False, None)]
    )

    return WebsiteListResponse(
        items=websites,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )


@router.post("/", response_model=WebsiteResponse, status_code=201)
async def create_website(
    website_in: WebsiteCreate,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> Any:
    """Create a new website to monitor."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    return await website.create_for_user(session, obj_in=website_in, user_id=user_id)


@router.get("/{website_id}", response_model=WebsiteWithChecks)
async def get_website(
    website_id: UUID,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
    include_checks: int = Query(
        10, ge=0, le=50, description="Number of recent checks to include"
    ),
) -> Any:
    """Get a specific website with recent checks."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    website_obj = await website.get_with_recent_checks(
        session,
        website_id=str(website_id),
        user_id=user_id,
        limit_checks=include_checks,
    )

    if not website_obj:
        raise HTTPException(status_code=404, detail="Website not found")

    # Get recent check timestamps
    recent_checks = await website_check.get_by_website(
        session, website_id=str(website_id), limit=include_checks
    )

    # Convert to response format
    response_data = WebsiteWithChecks.model_validate(website_obj)
    response_data.recent_checks = recent_checks

    if recent_checks:
        response_data.last_check_at = recent_checks[0].created_at
        # Find last change
        for check in recent_checks:
            if check.changes_detected:
                response_data.last_change_at = check.created_at
                break

    return response_data


@router.patch("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: UUID,
    website_update: WebsiteUpdate,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> Any:
    """Update a website's configuration."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    website_obj = await website.get_user_website(
        session, website_id=str(website_id), user_id=user_id
    )

    if not website_obj:
        raise HTTPException(status_code=404, detail="Website not found")

    # Handle ignore_selectors conversion to JSON
    update_data = website_update.model_dump(exclude_unset=True)
    if (
        "ignore_selectors" in update_data
        and update_data["ignore_selectors"] is not None
    ):
        import json

        update_data["ignore_selectors"] = json.dumps(update_data["ignore_selectors"])
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    return await website.update(session, db_obj=website_obj, obj_in=update_data)


@router.delete("/{website_id}")
async def delete_website(
    website_id: UUID,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> dict[str, str]:
    """Delete a website and all its checks."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    website_obj = await website.get_user_website(
        session, website_id=str(website_id), user_id=user_id
    )

    if not website_obj:
        raise HTTPException(status_code=404, detail="Website not found")

    await website.remove(session, id=website_id)
    return {"message": "Website deleted successfully"}


@router.get("/{website_id}/checks", response_model=WebsiteCheckListResponse)
async def get_website_checks(
    website_id: UUID,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """Get checks for a specific website."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # Verify user owns the website
    website_obj = await website.get_user_website(
        session, website_id=str(website_id), user_id=user_id
    )

    if not website_obj:
        raise HTTPException(status_code=404, detail="Website not found")

    checks = await website_check.get_by_website(
        session, website_id=str(website_id), skip=skip, limit=limit
    )

    # Get total count
    total = await website_check.get_count(
        session, filter_by=[("website_id", str(website_id), False, None)]
    )

    return WebsiteCheckListResponse(
        items=checks,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=math.ceil(total / limit) if total > 0 else 1,
    )


@router.post("/check", status_code=202)
async def trigger_website_check(
    check_trigger: CheckTrigger,
    background_tasks: BackgroundTasks,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> dict[str, str]:
    """Trigger manual website checks."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # If specific websites provided, verify user owns them
    if check_trigger.website_ids:
        for website_id in check_trigger.website_ids:
            website_obj = await website.get_user_website(
                session, website_id=str(website_id), user_id=user_id
            )
            if not website_obj:
                raise HTTPException(
                    status_code=404, detail=f"Website {website_id} not found"
                )

    # Add background task to trigger checks
    # This will be implemented in the worker service
    background_tasks.add_task(
        trigger_manual_check,
        user_id=user_id,
        website_ids=(
            [str(id) for id in check_trigger.website_ids]
            if check_trigger.website_ids
            else None
        ),
    )

    return {"message": "Check triggered successfully"}


@router.get("/dashboard/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> Any:
    """Get dashboard statistics and recent activity."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # Get user's websites count
    user_websites = await website.get_by_user(session, user_id=user_id, limit=1000)
    total_websites = len(user_websites)
    active_websites = len([w for w in user_websites if w.is_active])

    # Get check stats
    check_stats = await website_check.get_stats(session, user_id=user_id, days=30)

    # Count websites with changes in last 30 days
    recent_changes = await website_check.get_recent_changes(
        session, user_id=user_id, limit=100
    )
    websites_with_changes = len(set(check.website_id for check in recent_changes))

    stats = WebsiteStats(
        total_websites=total_websites,
        active_websites=active_websites,
        total_checks=check_stats["total_checks"],
        checks_last_24h=0,  # TODO: Implement 24h filter
        websites_with_changes=websites_with_changes,
        avg_response_time_ms=check_stats["avg_response_time_ms"],
    )

    # Get recent changes (last 10)
    recent_changes_limited = await website_check.get_recent_changes(
        session, user_id=user_id, limit=10
    )

    # Get failing websites
    failed_checks = await website_check.get_failed_checks(
        session, user_id=user_id, limit=10
    )
    failing_website_ids = set(check.website_id for check in failed_checks)
    failing_websites = [w for w in user_websites if str(w.id) in failing_website_ids]

    return DashboardResponse(
        stats=stats,
        recent_changes=recent_changes_limited,
        failing_websites=failing_websites[:5],  # Limit to 5
    )


# Notification settings routes
@router.get("/settings/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> Any:
    """Get user's notification settings."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    settings = await notification_settings.get_by_user(session, user_id=user_id)

    if not settings:
        # Return default settings
        return NotificationSettingsResponse(
            id=None,  # Will be set when first saved
            user_id=user_id,
            email_address=claims.get("email"),
            email_enabled=True,
            telegram_chat_id=None,
            telegram_enabled=False,
            telegram_bot_token=None,
            created_at=None,
            updated_at=None,
        )

    return settings


@router.put("/settings/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_update: NotificationSettingsUpdate,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> Any:
    """Update user's notification settings."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    return await notification_settings.upsert_for_user(
        session, obj_in=settings_update, user_id=user_id
    )


@router.post("/settings/notifications/test")
async def test_notification(
    channel: NotificationChannel,
    session: DBDep,
    claims: dict = Depends(auth0.require_auth()),
) -> dict[str, Any]:
    """Send a test notification to verify settings."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    from app.logic.notification_service import notification_service

    result = await notification_service.send_test_notification(
        user_id, channel, session
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": f"Test {channel.value} notification sent successfully"}


# Manual check function using the website checker
async def trigger_manual_check(user_id: str, website_ids: list[str] | None = None):
    """Trigger manual check using the website checker service."""
    from app.logic.website_checker import check_websites_for_user

    try:
        result = await check_websites_for_user(user_id, website_ids)
        print(f"Manual check completed for user {user_id}: {result}")
    except Exception as e:
        print(f"Error in manual check for user {user_id}: {e}")
