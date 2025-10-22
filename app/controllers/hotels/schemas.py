from datetime import datetime
from typing import Optional, List, get_type_hints
from pydantic import BaseModel, ConfigDict, create_model

from .enums import RoomType, RoomStatus
from ppgc_backend.app.schemas import AreaSchema
from ppgc_backend.app.schemas import CloudImageCreateSchema
from ppgc_backend.app.controllers.ratings.schemas import RatingResponseSchema


def make_optional_model(name: str, base_model: type[BaseModel]) -> type[BaseModel]:
    """Return a new model where all fields from `base_model` are optional."""
    annotations = get_type_hints(base_model)
    optional_fields = {
        k: (Optional[v], None) for k, v in annotations.items()
    }
    return create_model(name, __base__=base_model, **optional_fields)

class AllOptionalMeta(type(BaseModel)):
    def __new__(mcls, name, bases, namespace, **kwargs):
        annotations = namespace.get('__annotations__', {})
        for field, field_type in annotations.items():
            if not str(field_type).startswith('typing.Optional'):
                annotations[field] = Optional[field_type]
        return super().__new__(mcls, name, bases, namespace, **kwargs)

class OptionalBaseModel(BaseModel, metaclass=AllOptionalMeta):
    pass

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

class HotelUpdate(HotelBase):
    name: Optional[str] = None
    area: Optional[AreaSchema] = None
    description: Optional[str] = None
    cover_image: CloudImageCreateSchema
    other_images: Optional[List[CloudImageCreateSchema]] = None

class HotelResponse(HotelBase):
    id: int
    total_rooms: int
    manager_id: Optional[int] = None
    created_at: datetime
    receptionist_id: Optional[int] = None

class RoomBase(BaseModel):
    room_type: RoomType
    room_number: str
    price_per_night: float
    max_occupancy: int
    bed_count: Optional[int] = 1
    description: Optional[str] = None
    amenities: Optional[list[str]] = None
    cover_image: CloudImageCreateSchema
    other_images: Optional[List[CloudImageCreateSchema]] = None

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(RoomBase):
    pass

class RoomPatch(RoomBase):
    room_type: Optional[RoomType] = None
    room_number: Optional[str] = None
    price_per_night: Optional[float] = None
    max_occupancy: Optional[int] = None
    bed_count: Optional[int] = 1
    description: Optional[str] = None
    amenities: Optional[list[str]] = None
    cover_image: Optional[CloudImageCreateSchema] = None
    other_images: Optional[List[CloudImageCreateSchema]] = None
    status: Optional[RoomStatus] = "available"


class RoomResponse(RoomBase):
    id: int
    available: bool
    created_at: datetime
    status: RoomStatus