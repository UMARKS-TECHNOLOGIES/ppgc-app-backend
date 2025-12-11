"""
Savings services for creating and retrieving daily savings.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import datetime, timezone, timedelta
from ppgc_backend.app.controllers.savings.models import DailySavings
from ppgc_backend.app.controllers.savings.schemas import DailySavingsRequest, DailySavingsSchema, DailySavingsListResponse
from fastapi import HTTPException, status


async def create_daily_saving(
    user_id: int,
    saving_data: DailySavingsRequest,
    session: AsyncSession
) -> DailySavingsSchema:
    """
    Create a new daily savings record.
    
    Args:
        user_id: The ID of the user
        saving_data: DailySavingsRequest containing amount and name
        session: AsyncSession for database operations
    
    Returns:
        DailySavingsSchema: The created daily saving record
    """
    try:
        # Create new daily savings record
        new_saving = DailySavings(
            user_id=user_id,
            name=saving_data.name,
            amount=saving_data.amount,
        )
        session.add(new_saving)
        await session.commit()
        await session.refresh(new_saving)
        return new_saving
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create daily savings: {str(e)}"
        )


def get_date_range_for_period(period: str) -> tuple[datetime, datetime]:
    """
    Get start and end dates for a given period.
    
    Args:
        period: One of "this_week", "this_month", "this_year", "last_six_months"
    
    Returns:
        Tuple of (start_date, end_date)
    """
    now = datetime.now(timezone.utc)
    
    if period == "this_week":
        # Get Monday of current week
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    
    elif period == "this_month":
        # Get first day of current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    
    elif period == "this_year":
        # Get first day of current year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    
    elif period == "last_six_months":
        # Get date 6 months ago
        start_date = now - timedelta(days=180)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    
    else:
        raise ValueError(f"Invalid period: {period}. Must be one of: this_week, this_month, this_year, last_six_months")
    
    return start_date, end_date


async def get_daily_savings_by_period(
    user_id: int,
    period: str,
    session: AsyncSession
) -> DailySavingsListResponse:
    """
    Retrieve daily savings for a user within a specified period.
    
    Args:
        user_id: The ID of the user
        period: One of "this_week", "this_month", "this_year", "last_six_months"
        session: AsyncSession for database operations
    
    Returns:
        DailySavingsListResponse: List of daily savings with summary
    """
    try:
        # Get date range
        start_date, end_date = get_date_range_for_period(period)
        
        # Query daily savings for the period
        query = select(DailySavings).where(
            and_(
                DailySavings.user_id == user_id,
                DailySavings.created_at >= start_date,
                DailySavings.created_at <= end_date
            )
        ).order_by(DailySavings.created_at.desc())
        
        result = await session.execute(query)
        savings_records = result.scalars().all()
        
        # Calculate summary statistics
        total_amount = sum(saving.amount for saving in savings_records) if savings_records else 0.0
        transaction_count = len(savings_records)
        
        return DailySavingsListResponse(
            period=period,
            total_amount=total_amount,
            transaction_count=transaction_count,
            transactions=savings_records,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve daily savings: {str(e)}"
        )


async def get_all_daily_savings(
    user_id: int,
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0
) -> list[DailySavingsSchema]:
    """
    Retrieve all daily savings for a user with pagination.
    
    Args:
        user_id: The ID of the user
        session: AsyncSession for database operations
        limit: Number of records to return (default: 50)
        offset: Number of records to skip (default: 0)
    
    Returns:
        List of DailySavingsSchema
    """
    try:
        query = select(DailySavings).where(
            DailySavings.user_id == user_id
        ).order_by(
            DailySavings.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await session.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve daily savings: {str(e)}"
        )