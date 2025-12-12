from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict

from ppgc_backend.app.schemas import CloudImageCreateSchema
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice, ClientGenderChoice

class Refresh(BaseModel):
    id: int
    token: str

class UserResponseSchema(BaseModel):
    id: int
    email: str
    email_verified: bool
    user_role: UserRoleChoice
    created_at: datetime
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    email_notification: bool
    push_notification: bool
    gender: Optional[ClientGenderChoice] = None
    profile_avatar: Optional[CloudImageCreateSchema] = None
    access_token: Optional[str] = None
    refresh: Optional[Refresh] = None

    model_config = ConfigDict(from_attributes=True)