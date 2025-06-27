from typing import Optional
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import Investment, InvestmentTransaction

duration_map = {
    'monthly' : 30,
    'quarterly' : 91,
    'half_yearly' : 182,
    'yearly' : 365
}

def compute_rate(duration: int) -> int:
    """Takes in a duration in days and returns an agreed rate

    Args:
        duration (int): investment duration in days

    Returns:
        int: rate to apply
    """
    monthly = duration_map['monthly']
    quarterly = duration_map['quarterly']
    half_yearly = duration_map['half_yearly']
    yearly = duration_map['yearly']
    rate_map = {
        'monthly': 2,
        'quarterly': 10,
        'half_yearly': 15,
        'yearly': 30
    }


    rate = 0
    if quarterly > duration >= monthly:
        rate = rate_map['monthly']
    elif half_yearly > duration >= quarterly:
        rate = rate_map['quarterly']
    elif yearly > duration >= half_yearly:
        rate = rate_map['half_yearly']
    elif duration >= yearly:
        rate = rate_map['yearly']
    
    return rate

# ROI Formula: amount_invested * (interest_rate/100) * months
# 5% * amount_invested * months
# (5/100) * amount_invested * (amount_of_months_since_investment * 30 days)
def compute_roi(investment: Investment):
    rate = compute_rate(investment.duration)
    amount = investment.amount
    roi = ((rate / 100) * amount) + amount
    return roi



# Create new investment
async def create_investment(db: AsyncSession, user_id: int, investment_data: dict):
    new_investment = Investment(
        user_id=user_id, 
        **investment_data
    )
    db.add(new_investment)
    await db.commit()
    await db.refresh(new_investment)
    return new_investment


# Fetch a specific user investment (lazy ROI calculation)
async def get_user_investment(db: AsyncSession, investment_id: int):
    query = await db.execute(
        select(Investment).filter(Investment.id == investment_id)
    )
    investment = query.scalars().first()

    if not investment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment instance does not exist")
    
    # Compute ROI and maturity_date lazily
    investment.roi = compute_roi(investment)
    investment.maturity_date = investment.created_at + timedelta(days=investment.duration)

    return investment


# Fetch user investments (lazy ROI calculation)
async def get_user_investments(db: AsyncSession, user_id: int):
    query = select(Investment).where(Investment.user_id == user_id)
    result = await db.execute(query)
    investments = result.scalars().all()

    # Compute ROI lazily
    for investment in investments:
        investment.roi = compute_roi(investment)
        investment.maturity_date = investment.created_at + timedelta(days=investment.duration)

    return investments

# Deposit funds into an investment
async def deposit_funds_and_create_investment(
    db: AsyncSession,
    user_id: int,
    investment_data: dict,
):
    new_investment = Investment(
        user_id=user_id, 
        **investment_data
    )
    db.add(new_investment)
    await db.flush()

    # Add transaction record
    transaction = InvestmentTransaction(
        investment_id=new_investment.id,
        amount=new_investment.amount,
        transaction_type="deposit"
    )     
    
    db.add(transaction)
    await db.commit()
    await db.refresh(new_investment)
    return new_investment


# Withdraw funds (principal + ROI)
async def withdraw_funds(db: AsyncSession, investment_id: int):
    investment = await db.get(Investment, investment_id)
    if not investment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")

    roi = compute_roi(investment)
    total_amount = investment.amount + roi  # Principal + ROI

    # Log withdrawal
    transaction = InvestmentTransaction(
        investment_id=investment.id,
        amount=total_amount,
        transaction_type="withdraw"
    )

    investment.status = "completed"  # Mark as completed after withdrawal
    db.add(transaction)
    await db.commit()
    return total_amount