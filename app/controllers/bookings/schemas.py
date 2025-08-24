from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


from .enums import BookingStatus
from .models import Booking
from ppgc_backend.app.controllers.hotels.schemas import RoomResponse

class BookingBase(BaseModel):
    total_price: float
    room_id: int
    status: BookingStatus = BookingStatus.PENDING

    model_config = ConfigDict(from_attributes=True) 


class BookingCreate(BookingBase):
    occupancy_hours: int = Field(default=24, ge=24, description="Amount of hours for which the room is booked")


class BookingResponse(BookingBase):
    id: int
    created_at: datetime
    guest_count: int
    room: RoomResponse


    @classmethod
    def from_orm_with_relations(cls, booking: Booking) -> "BookingResponse":
        """Transform ORM object to response schema with all relationships resolved"""
        return cls(
            id=booking.id,
            check_in=booking.check_in,
            check_out=booking.check_out,
            guest_count=booking.room.max_occupancy,
            room=RoomResponse.model_validate(booking.room),
            created_at=booking.check_in,  # Assuming check_in is the created_at field
            total_price=booking.total_price,
            status=booking.status
        )   
