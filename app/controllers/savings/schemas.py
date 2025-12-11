"""
Savings schemas.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum


class SavingsType(str, PyEnum):
    """Types of savings activities"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTEREST = "interest"
    TRANSFER = "transfer"


class DailySavingsBase(BaseModel):
    """Savings base"""
    name: str
    amount: float

class DailySavingsRequest(DailySavingsBase):
    """Request to record daily savings"""
    pass


class DailySavingsSchema(DailySavingsBase):
    """Daily savings response schema"""
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavingsSummarySchema(BaseModel):
    """Savings summary response schema"""
    id: int
    user_id: int
    period: str  # "this_week", "this_month", "this_year", "last_six_months"
    total_savings: float
    total_deposits: float
    total_withdrawals: float
    transaction_count: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavingsSummaryResponse(BaseModel):
    """Response containing multiple savings summaries"""
    this_week: Optional[SavingsSummarySchema] = None
    this_month: Optional[SavingsSummarySchema] = None
    this_year: Optional[SavingsSummarySchema] = None
    last_six_months: Optional[SavingsSummarySchema] = None
    recent_transactions: List[DailySavingsSchema] = []


class DailySavingsListResponse(BaseModel):
    """Response containing list of daily savings with filtering"""
    period: str
    total_amount: float
    transaction_count: int
    transactions: List[DailySavingsSchema] = []
    
    model_config = ConfigDict(from_attributes=True)
