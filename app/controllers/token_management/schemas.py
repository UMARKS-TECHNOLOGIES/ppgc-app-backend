"""
Token management schemas.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str


class RefreshTokenSchema(BaseModel):
    """Refresh token response schema"""
    id: int
    user_id: int
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AccessTokenSchema(BaseModel):
    """Access token response schema"""
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_revoked: bool
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SessionLogSchema(BaseModel):
    """Session log response schema"""
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_time: datetime
    logout_time: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class LogoutRequest(BaseModel):
    """Request to logout user"""
    refresh_token: Optional[str] = None
    logout_all_sessions: bool = False
