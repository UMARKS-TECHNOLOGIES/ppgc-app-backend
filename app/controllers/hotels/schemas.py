from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


from ppgc_backend.app.schemas.area_schema import AreaSchema
from ppgc_backend.app.controllers.ratings.schemas import RatingResponseSchema

class OptionalBaseModel(BaseModel):
    """Automatically makes all fields optional in subclasses."""
    def __init_subclass__(cls, **kwargs):
        for field in cls.__annotations__:
            cls.__annotations__[field] = Optional[cls.__annotations__[field]]


class RoomTypeEnum(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    DELUXE = "deluxe"
    FAMILY = "family"

class HotelImageFmt(BaseModel):
    public_id: str
    secure_url: str

class HotelBase(BaseModel):
    name: str
    area: AreaSchema
    description: Optional[str] = None
    cover_image: HotelImageFmt
    other_images: Optional[list[HotelImageFmt]] = None
    
    model_config = ConfigDict(from_attributes=True)


class HotelCreate(HotelBase):
    pass

class HotelUpdate(OptionalBaseModel):
    name: Optional[str] = None
    area: Optional[AreaSchema] = None
    description: Optional[str] = None
    cover_image: Optional[HotelImageFmt] = None
    other_images: Optional[list[HotelImageFmt]] = None

class HotelResponse(HotelBase):
    id: int
    created_at: datetime
    total_rooms: int

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
