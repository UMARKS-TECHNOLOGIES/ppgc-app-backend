from typing import Optional
from sqlalchemy.future import select
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import Investment, InvestmentTransaction

# ROI Formula: amount_invested * (interest_rate/100) * months
# 5% * amount_invested * months
# (5/100) * amount_invested * (amount_of_months_since_investment * 30 days)
def compute_roi(investment: Investment):
    duration = (datetime.now(timezone.utc) - investment.created_at).days / 30  # months
    roi = investment.investment_amount * (investment.interest_rate / 100) * duration
    return roi

# Create new investment
async def create_investment(db: AsyncSession, user_id: int, amount: float, interest_rate: float = 5.0):
    new_investment = Investment(user_id=user_id, investment_amount=amount, interest_rate=interest_rate)
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
    
    # Compute ROI lazily
    investment.roi = compute_roi(investment)

    return investment


# Fetch user investments (lazy ROI calculation)
async def get_user_investments(db: AsyncSession, user_id: int):
    query = select(Investment).where(Investment.user_id == user_id)
    result = await db.execute(query)
    investments = result.scalars().all()

    # Compute ROI lazily
    for investment in investments:
        investment.roi = compute_roi(investment)

    return investments

# Deposit funds into an investment
async def deposit_funds(db: AsyncSession, user_id: int, investment_id: Optional[int], amount: float):
    if investment_id:
        # Fetch the existing investment
        investment = await db.get(Investment, investment_id)
        if not investment:
            return None  # Return None if investment_id is invalid
    else:
        # Create a new investment if no investment_id is provided
        # flush to get an investment id
        investment = Investment(user_id=user_id, investment_amount=amount)
        db.add(investment)
        await db.flush()

    # Add transaction record
    transaction = InvestmentTransaction(
        investment_id=investment.id,
        amount=amount,
        transaction_type="deposit"
    )


    # Update investment balance only if it's an existing investment
    if investment_id:
        investment.investment_amount += amount      
    
    db.add(transaction)
    await db.commit()
    await db.refresh(investment)
    return investment


# Withdraw funds (principal + ROI)
async def withdraw_funds(db: AsyncSession, investment_id: int):
    investment = await db.get(Investment, investment_id)
    if not investment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")

    roi = compute_roi(investment)
    total_amount = investment.investment_amount + roi  # Principal + ROI

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