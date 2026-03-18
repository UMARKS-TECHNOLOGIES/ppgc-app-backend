from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Body, status

from .services import (
    require_owner,
    delete_investment,
    create_investment,
    get_user_investment,
    get_user_investments,
    update_investment_status,
)
from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.actors.models import User
from .schemas import InvestmentCreate, InvestmentResp, PatchInvestmentStatus
from ppgc_backend.app.controllers.auth.services import decode_user_from_token


router = APIRouter(prefix='/investments', tags=["investments"])


@router.post('/create/', response_model = InvestmentResp)
async def create_investment_endpoint(
    data: InvestmentCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    return await create_investment(db, user.id, data)


@router.get('/{investment_id}/', response_model = InvestmentResp)
async def get_user_investment_endpoint(
    investment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_owner),
):
    return await get_user_investment(db, investment_id, user.id)


@router.get('/', response_model = List[InvestmentResp])
async def get_user_investments_endpoint(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    return await get_user_investments(db, user.id)


@router.patch('/{investment_id}/', response_model = InvestmentResp)
async def patch_investment_status_endpoint(
    investment_id: int,
    data: PatchInvestmentStatus,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_owner),
):
    return await update_investment_status(db, user.id, investment_id, data.status)


@router.delete('/{investment_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def patch_investment_status_endpoint(
    investment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    return await delete_investment(db, investment_id)