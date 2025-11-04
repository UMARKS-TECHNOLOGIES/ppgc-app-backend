from datetime import datetime
from pydantic import BaseModel, condecimal, ConfigDict, Field

from .enums import InvestmentStatus
from ppgc_backend.app.controllers.transactions.schemas import DepositSchema, TrxResponse

class InvestmentBase(BaseModel):
    name: str
    amount: float
    interest_rate: float = Field(..., description="Interest rate on initial investment. i.e 3.12 ~ 3.12%")
    duration: int = Field(..., description="Investment duration in days")
    trx: DepositSchema

class InvestmentCreate(InvestmentBase):
    pass

class InvestmentResp(InvestmentBase):
    id: int
    trx: TrxResponse
    created_at: datetime
    roi: int
    maturity_time: datetime
    status: InvestmentStatus

class PatchInvestmentStatus(BaseModel):
    status: InvestmentStatus