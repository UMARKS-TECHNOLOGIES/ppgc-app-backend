from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


from .enums import BookingStatus
from .models import Booking
from ppgc_backend.app.controllers.hotels.schemas import RoomResponse

class BookingBase(BaseModel):
    total_price: float
    room_id: int
    status: BookingStatus = BookingStatus.pending
    guests: int = 1

    model_config = ConfigDict(from_attributes=True) 


class BookingCreate(BookingBase):
    occupancy_hours: int = Field(default=24, ge=24, description="Amount of hours for which the room is booked")


class BookingResponse(BookingBase):
    id: int
    check_in: datetime
    check_out: datetime

class BookingUpdate(BaseModel):
    total_price: Optional[float] = None
    room_id: Optional[int] = None
    status: Optional[BookingStatus] = None
    guests: Optional[int] = None
    occupancy_hours: Optional[int] = None