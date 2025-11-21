from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


from .enums import BookingStatus
from .models import Booking
from ppgc_backend.app.controllers.hotels.schemas import RoomResponse

class BookingBase(BaseModel):
    guest_name: str = Field(..., description="Name of the guest")
    phone: str = Field(..., description="Phone number of the guest")
    email: str = Field(..., description="Email of the guest")
    price_per_night: float = Field(..., gt=0, description="Price per night")
    paid_amount: float = Field(default=0.0, ge=0, description="Amount already paid by guest")
    notes: Optional[str] = Field(default=None, description="Additional notes about the booking")
    room_id: int = Field(..., description="Room ID being booked")
    hotel_id: int = Field(..., description="Hotel ID")
    total_number_of_days: int = Field(..., gt=0, description="Total number of days for stay")
    total_amount: float = Field(..., gt=0, description="Total amount for the booking")
    balance_payment: float = Field(..., ge=0, description="Balance payment remaining")
    status: BookingStatus = BookingStatus.pending
    guests: int = Field(default=1, ge=1, description="Number of guests")

    model_config = ConfigDict(from_attributes=True) 


class BookingCreate(BookingBase):
    check_in: datetime = Field(..., description="Check-in date and time")
    check_out: datetime = Field(..., description="Check-out date and time")


class BookingResponse(BaseModel):
    id: int
    guest_name: str
    phone: str
    email: str
    check_in: datetime
    check_out: datetime
    price_per_night: float
    paid_amount: float
    notes: Optional[str]
    room_id: int
    hotel_id: int
    total_number_of_days: int
    total_amount: float
    balance_payment: float
    status: BookingStatus
    guests: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BookingUpdate(BaseModel):
    guest_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    price_per_night: Optional[float] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None
    room_id: Optional[int] = None
    hotel_id: Optional[int] = None
    total_number_of_days: Optional[int] = None
    total_amount: Optional[float] = None
    balance_payment: Optional[float] = None
    status: Optional[BookingStatus] = None
    guests: Optional[int] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None