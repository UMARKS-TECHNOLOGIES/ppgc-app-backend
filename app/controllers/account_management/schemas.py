"""
Account management schemas.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeactivateAccountRequest(BaseModel):
    """Request to deactivate account"""
    reason: Optional[str] = None


class ReactivateAccountRequest(BaseModel):
    """Request to reactivate account"""
    token: str


class AccountDeactivationSchema(BaseModel):
    """Account deactivation response schema"""
    id: int
    user_id: int
    is_deactivated: bool
    deactivated_at: Optional[datetime] = None
    can_reactivate_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountSettingsRequest(BaseModel):
    """Request to update account settings"""
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    privacy_level: Optional[str] = None
    show_activity: Optional[bool] = None
    allow_messages: Optional[bool] = None


class AccountSettingsSchema(BaseModel):
    """Account settings response schema"""
    id: int
    user_id: int
    email_notifications: bool
    push_notifications: bool
    marketing_emails: bool
    two_factor_enabled: bool
    privacy_level: str
    show_activity: bool
    allow_messages: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
