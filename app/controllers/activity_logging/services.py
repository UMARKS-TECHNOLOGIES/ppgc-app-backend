"""
Services for activity logging: create logs, query history, and generate statistics.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from fastapi import HTTPException, status

from .models import ActivityLog, ActivityStatusChoice
from ppgc_backend.app.controllers.actors.models import User
from .schemas import ActivityLogCreateSchema, ActivityLogResponseSchema, ActivityStatisticsSchema


async def log_activity(
    db: AsyncSession,
    user: User,
    action: str,
    status: ActivityStatusChoice = ActivityStatusChoice.pending,
    session_id: Optional[int] = None,
    method: Optional[str] = None,
    endpoint: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_body: Optional[str] = None,
    response_status_code: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    description: Optional[str] = None,
) -> ActivityLog:
    """
    Create and log a user activity.
    
    Args:
        db: AsyncSession for database operations
        user: The user performing the activity
        action: Action name (e.g., "POST /auth/signin")
        status: Activity status (success, failed, pending, error)
        session_id: Optional session log ID
        method: HTTP method
        endpoint: API endpoint path
        ip_address: Client IP address
        user_agent: Client user agent
        request_body: Sanitized request payload
        response_status_code: HTTP response status
        response_time_ms: Response time in milliseconds
        description: Additional details
        
    Returns:
        ActivityLog object
    """
    activity = ActivityLog(
        user_id=user.id,
        session_id=session_id,
        action=action,
        status=status,
        description=description,
        method=method,
        endpoint=endpoint,
        ip_address=ip_address,
        user_agent=user_agent,
        request_body=request_body,
        response_status_code=response_status_code,
        response_time_ms=response_time_ms,
        timestamp=datetime.now(timezone.utc)
    )
    
    db.add(activity)
    await db.commit()
    
    return activity


async def get_user_activities(
    db: AsyncSession,
    user: User,
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[ActivityStatusChoice] = None,
    days: Optional[int] = None,
) -> tuple[List[ActivityLogResponseSchema], int]:
    """
    Retrieve activities for a user with optional filtering.
    
    Args:
        db: AsyncSession for database operations
        user: The user whose activities to retrieve
        limit: Number of records to return
        offset: Number of records to skip
        status_filter: Filter by activity status
        days: Retrieve activities from last N days
        
    Returns:
        Tuple of (list of activities, total count)
    """
    query = select(ActivityLog).where(ActivityLog.user_id == user.id)
    
    # Filter by status if provided
    if status_filter:
        query = query.where(ActivityLog.status == status_filter)
    
    # Filter by days if provided
    if days:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.where(ActivityLog.timestamp >= cutoff_date)
    
    # Get total count
    count_query = select(func.count(ActivityLog.id)).where(ActivityLog.user_id == user.id)
    if status_filter:
        count_query = count_query.where(ActivityLog.status == status_filter)
    if days:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        count_query = count_query.where(ActivityLog.timestamp >= cutoff_date)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Execute paginated query
    query = query.order_by(ActivityLog.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return activities, total


async def get_activity_statistics(
    db: AsyncSession,
    user: User,
    days: Optional[int] = None,
) -> ActivityStatisticsSchema:
    """
    Generate activity statistics for a user.
    
    Args:
        db: AsyncSession for database operations
        user: The user to generate stats for
        days: Statistics for last N days (None = all time)
        
    Returns:
        ActivityStatisticsSchema with statistics
    """
    base_query = select(ActivityLog).where(ActivityLog.user_id == user.id)
    
    if days:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        base_query = base_query.where(ActivityLog.timestamp >= cutoff_date)
    
    # Get all activities
    result = await db.execute(base_query)
    all_activities = result.scalars().all()
    
    total = len(all_activities)
    successful = sum(1 for a in all_activities if a.status == ActivityStatusChoice.success)
    failed = sum(1 for a in all_activities if a.status == ActivityStatusChoice.failed)
    pending = sum(1 for a in all_activities if a.status == ActivityStatusChoice.pending)
    error = sum(1 for a in all_activities if a.status == ActivityStatusChoice.error)
    
    # Calculate success rate
    success_rate = (successful / total * 100) if total > 0 else 0
    
    # Find most common action
    action_counts = {}
    for activity in all_activities:
        action_counts[activity.action] = action_counts.get(activity.action, 0) + 1
    
    most_common_action = max(action_counts, key=action_counts.get) if action_counts else None
    
    return ActivityStatisticsSchema(
        total_activities=total,
        successful=successful,
        failed=failed,
        pending=pending,
        error=error,
        most_common_action=most_common_action,
        success_rate=round(success_rate, 2)
    )


async def update_activity_status(
    db: AsyncSession,
    activity_id: int,
    status: ActivityStatusChoice,
    response_status_code: Optional[int] = None,
    response_time_ms: Optional[int] = None,
) -> ActivityLog:
    """
    Update an activity's status after the action completes.
    
    Args:
        db: AsyncSession for database operations
        activity_id: ID of the activity to update
        status: New status
        response_status_code: HTTP response status
        response_time_ms: Response time in milliseconds
        
    Returns:
        Updated ActivityLog
    """
    query = select(ActivityLog).where(ActivityLog.id == activity_id)
    result = await db.execute(query)
    activity = result.scalars().first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )
    
    activity.status = status
    if response_status_code:
        activity.response_status_code = response_status_code
    if response_time_ms:
        activity.response_time_ms = response_time_ms
    
    db.add(activity)
    await db.commit()
    
    return activity
