from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict

from ppgc_backend.app.schemas import CloudImageCreateSchema
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice, ClientGenderChoice

class Refresh(BaseModel):
    id: int
    token: Optional[str] = None

class UserResponseSchema(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    other_names: Optional[str] = None
    email_verified: bool
    gender: Optional[ClientGenderChoice] = None
    date_of_birth: Optional[date] = None
    nin: Optional[str] = None
    dial_code: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    email_notification: bool
    push_notification: bool
    user_role: UserRoleChoice
    created_at: datetime
    profile_avatar: Optional[CloudImageCreateSchema] = None
    access_token: Optional[str] = None
    refresh: Optional[Refresh] = None
    #recovery_email_verified: bool = False

    model_config = ConfigDict(from_attributes=True)