"""
Schemas for settings endpoints
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from ppgc_backend.app.controllers.auth.services import EmailEtCodeSchema


class RecoveryEmailRequestSchema(BaseModel):
    """Schema for requesting a recovery email change"""
    recovery_email: EmailStr = Field(..., description="New recovery email address")

    model_config = {
        "json_schema_extra": {
            "example": {
                "recovery_email": "recovery@example.com"
            }
        }
    }


class RecoveryEmailVerificationSchema(EmailEtCodeSchema):
    """Schema for confirming recovery email with verification code"""
    pass


class RecoveryEmailResponseSchema(BaseModel):
    """Schema for recovery email response"""
    detail: str
    recovery_email: Optional[str] = None
    verified: Optional[bool] = None
    expiry: Optional[str] = None

    model_config = {
        "json_schema_extra" : {
            "example": {
                "detail": "Verification code sent to recovery email",
                "expiry": "2025-12-11T12:30:00+00:00"
            }
        }
    }


class UserSettingsBase(BaseModel):
    """Schema for user settings"""
    first_name: str
    last_name: str
    other_names: Optional[str] = None
    gender: Optional[str] = None
    nin: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    dial_code: Optional[str] = None
    phone_number: Optional[str] = None
    adress: Optional[str] = None
    email_notification: bool = True
    push_notification: bool = True

    model_config = ConfigDict(from_attributes = True)

class UserSettingsSchema(UserSettingsBase):
    """Schema for user settings"""
    pass

class UserSettingsResponseSchema(UserSettingsBase):
    """Schema for user settings"""
    recovery_email_verified: bool = False
    pass
