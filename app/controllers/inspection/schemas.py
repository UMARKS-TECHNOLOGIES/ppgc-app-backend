from datetime import date, time
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

from .enums import InspectionStatus

class InspectionCreate(BaseModel):
    call_number: str
    property_id: int
    date_of_inspection: date
    time_of_inspection: time
    
    property_name: str
    fullname: Optional[str] = Field(None, description="If not provided, would be inferred from the requester's name")
    requester_id: Optional[int] = Field(None, description="If not provided, would be inferred from the requester")

    model_config = ConfigDict(from_attributes=True) 

class InspectionResponse(BaseModel):
    id: int
    fullname: str
    call_number: str
    property_name: str
    date_of_inspection: date
    time_of_inspection: time
    requester_id: Optional[int] = None
    asset_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True) 

class InspectionUpdate(BaseModel):
    status: Optional[Literal['completed','cancelled','pending','confirmed']] = None
    date_of_inspection: Optional[date] = None
    time_of_inspection: Optional[time] = None