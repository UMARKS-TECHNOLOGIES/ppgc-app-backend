from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from ppgc_backend.app.schemas.area_schema import AreaSchema
from ppgc_backend.app.schemas import CloudImageCreateSchema

class PropertyBase(BaseModel):
    title: str
    price: Decimal
    description: Optional[str] = None
    availability: str = "available"
    type: str
    cover_image: CloudImageCreateSchema
    other_images: Optional[List[CloudImageCreateSchema]] = None
    features: Optional[List[str]] = None
    area: AreaSchema


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(PropertyBase):
    title: Optional[str] = None
    price: Optional[Decimal] = None
    availability: Optional[str] = None
    type: Optional[str] = None
    cover_image: Optional[CloudImageCreateSchema] = None
    area: Optional[AreaSchema] = None


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)