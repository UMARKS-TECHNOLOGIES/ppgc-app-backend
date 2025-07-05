from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


from ppgc_backend.app.schemas.area_schema import AreaSchema
from ppgc_backend.app.controllers.ratings.schemas import RatingResponseSchema


class RoomTypeEnum(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    DELUXE = "deluxe"
    FAMILY = "family"


class HotelBase(BaseModel):
    name: str
    area: AreaSchema
    description: Optional[str] = None
    cover_image_url: str
    other_image_urls: Optional[list[str]] = None
    
    model_config = ConfigDict(from_attributes=True)


class HotelCreate(HotelBase):
    pass

class HotelResponse(HotelBase):
    id: int
    created_at: datetime
    total_rooms: int
    ratings: Optional[list[RatingResponseSchema]]


class RoomBase(BaseModel):
    room_type: RoomTypeEnum
    price_per_night: float
    max_occupancy: int

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(RoomBase):
    hotel_id: int


class RoomResponse(RoomBase):
    id: int
    available: bool
    created_at: datetime
