from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.auth import (
    decode_user_from_token,
)
from ppgc_backend.app.schemas.auth_schemas import (
    TokenData, 
)
from ppgc_backend.app.controllers.investments.schemas import InvestmentDeposit, InvestmentResponse, DepositRequest, WithdrawRequest
from ppgc_backend.app.controllers.investments.roi import (
    withdraw_funds,
    get_user_investment,
    get_user_investments, 
    deposit_funds_and_create_investment, 
)


router = APIRouter(prefix="/roi", tags=["roi"])


# Create investment
@router.post("/create-investment", response_model=InvestmentResponse)
async def create_new_investment(
    investment: InvestmentDeposit, 
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(decode_user_from_token)
):
    return await deposit_funds_and_create_investment(
        db, 
        current_user.id, 
        investment.model_dump()
    )


# Get a specific investment (ROI is computed lazily)
@router.get("/get-investment/{investment_id}", response_model=InvestmentResponse)
async def get_investments(
    investment_id: int,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(decode_user_from_token)
):
    return await get_user_investment(db, investment_id)


# Get investments (ROI is computed lazily)
@router.get("/get-investments", response_model=list[InvestmentResponse])
async def get_investments(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(decode_user_from_token)
):
    return await get_user_investments(db, current_user.id)


# Withdraw funds (ROI included)
@router.get("/withdraw/{investment_id}")
async def withdraw(
    investment_id: int, 
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(decode_user_from_token)
)->float:
    return await withdraw_funds(db, investment_id)
