from datetime import datetime
from pydantic import BaseModel

from .enums import TRXType

class TrxBase(BaseModel):
    amount: float
    name: str
    trx_id: str


class DepositSchema(TrxBase):
    trx_type: TRXType =  TRXType.deposit


class WithdrawSchema(TrxBase):
    trx_type: TRXType =  TRXType.withdraw


class TrxResponse(TrxBase):
    id: int
    trx_type: TRXType
    created_at: datetime