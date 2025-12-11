"""
Two-factor authentication schemas.
"""
from datetime import datetime
from .enums import TwoFAMethods
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field
from ppgc_backend.app.controllers.auth.schemas import PinOrPasswordSchema

class Enable2FARequest(BaseModel):
    """Request to enable 2FA"""
    method: TwoFAMethods = Field(..., description="totp or sms")
    phone_number: Optional[str] = Field(None, description="Required for SMS method")


class Setup2FAResponse(BaseModel):
    """Response for 2FA setup with secret"""
    secret: str = Field(..., description="Base32 encoded TOTP secret")
    qr_code_url: Optional[str] = Field(None, description="QR code URL for TOTP setup")
    backup_codes: List[str] = Field(default_factory=list, description="Backup codes for account recovery")
    method: TwoFAMethods


class Verify2FARequest(BaseModel):
    """Request to verify 2FA code"""
    code: str = Field(..., description="6-digit TOTP code or one-time password")


class Verify2FAResponse(BaseModel):
    """Response after verifying 2FA"""
    verified: bool
    message: str


class TwoFactorAuthSchema(BaseModel):
    """Two-factor auth response schema"""
    id: int
    user_id: int
    is_enabled: bool
    method: str
    verified: bool
    phone_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TwoFactorAuthLogSchema(BaseModel):
    """Two-factor auth log response schema"""
    id: int
    user_id: int
    attempt_type: str
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Disable2FARequest(PinOrPasswordSchema):
    """Request to disable 2FA"""
    pass


class GenerateBackupCodesRequest(PinOrPasswordSchema):
    """Request to generate new backup codes"""
    pass