from typing import Optional
from pydantic import BaseModel

class BankAccBase(BaseModel):
    account_number: str
    account_name: str
    bank_name: str
    bank_code: Optional[str] = None
    currency: str


class BankAccCreate(BankAccBase):
    pass


class BankAccPatch(BankAccBase):
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    currency: Optional[str] = None


class BankAccResp(BankAccBase):
    id: int