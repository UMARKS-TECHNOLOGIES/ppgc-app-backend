from pydantic import BaseModel, condecimal, ConfigDict
from datetime import datetime
from typing import Optional, Annotated, List

# Create investment request
class InvestmentCreate(BaseModel):
    investment_amount: Annotated[float, condecimal(gt=0)]
    interest_rate: Annotated[float, condecimal(gt=0)]

class InvestmentTransactionSchema(BaseModel):
    id: int
    amount: Annotated[float, condecimal(gt=0)]
    transaction_type: str
    created_at: datetime
    pass

# Response schema for investment details
class InvestmentResponse(BaseModel):
    id: int
    status: str
    investment_amount: float
    interest_rate: float
    created_at: datetime
    updated_at: datetime
    roi: Optional[float] = 0.0  # Computed lazily

    transactions: Optional[List[InvestmentTransactionSchema]]

    model_config = ConfigDict(from_attributes=True)


# Deposit funds request
class DepositRequest(BaseModel):
    investment_id: Optional[int]
    amount: Annotated[float, condecimal(gt=0)]

# Withdraw funds request
class WithdrawRequest(BaseModel):
    investment_id: int
