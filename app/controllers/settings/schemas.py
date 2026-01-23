"""
Schemas for settings endpoints
"""
from datetime import date
from typing import Optional
from ppgc_backend.app.schemas import CloudImageCreateSchema
from ppgc_backend.app.controllers.auth.schemas import EmailEtCodeSchema
from ppgc_backend.app.controllers.actors.schemas import UserResponseSchema
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    other_names: Optional[str] = None
    gender: Optional[str] = None
    nin: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    email_notification: bool = True
    push_notification: bool = True
    profile_avatar: Optional[CloudImageCreateSchema] = None

    model_config = ConfigDict(from_attributes = True)

    @field_validator("nin")
    @classmethod
    def validate_nin(cls, v):
        if v is not None and len(v) != 11:
            raise ValueError("NIN must be exactly 11 characters long")
        return v

    @field_validator("pass_code", check_fields=False)
    @classmethod
    def validate_pass_code(cls, v):
        if v is not None and len(v) != 4:
            raise ValueError("Pass code must be exactly 4 characters long")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if v is not None and len(v) != 10:
            raise ValueError("Phone number must be exactly 10 characters long")
        return v

class UserSettingsSchema(UserSettingsBase):
    """Schema for user settings"""
    pass

class UserSettingsResponseSchema(UserResponseSchema):
    """Schema for user settings"""
    dial_code: Optional[str] = None 
    pass
