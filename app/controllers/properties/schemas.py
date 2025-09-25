from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from ppgc_backend.app.schemas.area_schema import AreaSchema
from ppgc_backend.app.schemas.asset_schemas import CloudImageCreateSchema

class PropertyBase(BaseModel):
    title: str
    price: Decimal
    description: Optional[str] = None
    availability: str = "available"
    type: str
    cover_image: CloudImageCreateSchema
    other_images: Optional[List[CloudImageCreateSchema]] = None
    features: Optional[dict] = None
    area: AreaSchema


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    availability: Optional[str] = None
    type: Optional[str] = None
    cover_image: Optional[int] = None
    other_images: Optional[int] = None
    features: Optional[dict] = None
    area: Optional[int] = None


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
