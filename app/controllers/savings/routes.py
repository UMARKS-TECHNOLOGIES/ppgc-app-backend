"""
Savings routes for creating and retrieving daily savings.
"""
from typing import Literal
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.models import User
from ppgc_backend.app.controllers.auth.services import decode_user_from_token
from ppgc_backend.app.controllers.savings.schemas import (
    DailySavingsRequest,
    DailySavingsSchema,
    DailySavingsListResponse
)
from ppgc_backend.app.controllers.savings.services import (
    create_daily_saving,
    get_daily_savings_by_period,
    get_all_daily_savings,
)

router = APIRouter(prefix="/savings", tags=["savings"])


@router.post("/create", response_model=DailySavingsSchema, status_code=status.HTTP_201_CREATED)
async def create_saving(
    saving_data: DailySavingsRequest,
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Create a new daily savings record.
    
    Args:
        saving_data: DailySavingsRequest containing amount and name
        current_user: The authenticated user
        session: Database session
    
    Returns:
        DailySavingsSchema: The created saving record
    """
    return await create_daily_saving(
        user_id=current_user.id,
        saving_data=saving_data,
        session=session
    )


@router.get("/period", response_model=DailySavingsListResponse)
async def get_savings_by_period(
    period: Literal["this_week", "this_month", "this_year", "last_six_months"] =  Query(..., description="Period: this_week, this_month, this_year, or last_six_months"),
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve daily savings for a specific period.
    
    Args:
        period: One of "this_week", "this_month", "this_year", "last_six_months"
        current_user: The authenticated user
        session: Database session
    
    Returns:
        DailySavingsListResponse: List of savings with summary
    """
    return await get_daily_savings_by_period(
        user_id=current_user.id,
        period=period,
        session=session
    )


@router.get("/all", response_model=list[DailySavingsSchema])
async def get_all_savings(
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve all daily savings for the authenticated user with pagination.
    
    Args:
        limit: Number of records to return (default: 50, max: 100)
        offset: Number of records to skip (default: 0)
        current_user: The authenticated user
        session: Database session
    
    Returns:
        List of DailySavingsSchema
    """
    return await get_all_daily_savings(
        user_id=current_user.id,
        session=session,
        limit=limit,
        offset=offset
    )