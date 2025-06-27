from pydantic import BaseModel, condecimal, ConfigDict
from datetime import datetime
from typing import Optional, Annotated, List, Literal

# Create investment request
class InvestmentCreate(BaseModel):
    amount: Annotated[float, condecimal(gt=0)]
    name: Optional[Annotated[float, condecimal(gt=0)]] = None
    interest_rate: Literal['2%','10%','15%','30%']
    duration: int

class InvestmentDeposit(InvestmentCreate):
    pass

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
    interest_rate: str
    created_at: datetime
    updated_at: datetime
    maturity_date: datetime
    investment_amount: float
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
