"""
Routes for activity logging endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from .enums import ActivityStatusChoice
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import decode_user_from_token
from .schemas import ActivityLogListResponseSchema, ActivityStatisticsSchema
from .services import (
    get_user_activities,
    get_activity_statistics,
)

router = APIRouter(prefix='/activity-logs', tags=['activity-logs'])


@router.get('/my-activities/', response_model=ActivityLogListResponseSchema)
async def get_my_activities(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: ActivityStatusChoice = Query(None, description="Filter by activity status"),
    days: int = Query(None, ge=1, description="Activities from last N days"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """
    Retrieve paginated activity logs for the authenticated user.
    
    Query Parameters:
        - page: Page number (default 1)
        - size: Number of items per page (default 20, max 100)
        - status: Filter by status (success, failed, pending, error)
        - days: Retrieve activities from last N days
    """
    offset = (page - 1) * size
    activities, total = await get_user_activities(
        db, user, limit=size, offset=offset, status_filter=status, days=days
    )
    
    return {
        "total": total,
        "count": len(activities),
        "page": page,
        "size": size,
        "items": activities
    }


# @router.get('/statistics', response_model=ActivityStatisticsSchema)
async def get_activity_stats(
    days: int = Query(None, ge=1, description="Statistics for last N days"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """
    Get activity statistics for the authenticated user.
    
    Query Parameters:
        - days: Statistics for last N days (None = all time)
    
    Returns:
        - total_activities: Total number of logged activities
        - successful: Count of successful activities
        - failed: Count of failed activities
        - pending: Count of pending activities
        - error: Count of error activities
        - most_common_action: Most frequently logged action
        - success_rate: Success rate as percentage
    """
    return await get_activity_statistics(db, user, days=days)
