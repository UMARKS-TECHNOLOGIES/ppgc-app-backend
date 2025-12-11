"""
Two-factor authentication services.
"""
import pyotp
import qrcode
from io import BytesIO
import base64
import secrets
from sqlalchemy.future import select
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from .schemas import Disable2FARequest, GenerateBackupCodesRequest
from ppgc_backend.app.controllers.auth.services import verify_pin_or_password
from ppgc_backend.app.controllers.two_factor_auth.models import TwoFactorAuth, TwoFactorAuthLog
from ppgc_backend.app.controllers.two_factor_auth.schemas import (
    TwoFactorAuthSchema,
    Setup2FAResponse,
    Verify2FAResponse,
)
from ppgc_backend.app.models import User
from ppgc_backend.app.controllers.auth.services import verify_password


async def get_user_2fa_settings(
    user_id: int,
    session: AsyncSession
) -> TwoFactorAuth:
    """
    Retrieve 2FA settings for a user.
    
    Args:
        user_id: The user ID
        session: AsyncSession for database operations
    
    Returns:
        TwoFactorAuth model or None if not found
    """
    query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().first()


def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret.
    
    Returns:
        Base32 encoded secret
    """
    return pyotp.random_base32()


def generate_backup_codes(count: int = 10) -> list[str]:
    """
    Generate backup codes for account recovery.
    
    Args:
        count: Number of backup codes to generate
    
    Returns:
        List of backup codes
    """
    return [secrets.token_hex(4).upper() for _ in range(count)]


def generate_qr_code(secret: str, email: str, app_name: str = "PPGC") -> str:
    """
    Generate QR code for TOTP setup.
    
    Args:
        secret: TOTP secret
        email: User's email
        app_name: Application name
    
    Returns:
        Base64 encoded QR code image
    """
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=email, issuer_name=app_name)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


async def setup_totp_2fa(
    user_id: int,
    session: AsyncSession,
    email: str
) -> Setup2FAResponse:
    """
    Set up TOTP-based 2FA for a user.
    
    Args:
        user_id: The user ID
        session: AsyncSession for database operations
        email: User's email for QR code
    
    Returns:
        Setup2FAResponse with secret and backup codes
    """
    try:
        # Check if 2FA already exists
        existing_2fa = await get_user_2fa_settings(user_id, session)
        
        if existing_2fa and existing_2fa.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled for this user"
            )
        
        # Generate secret and backup codes
        secret = generate_totp_secret()
        backup_codes = generate_backup_codes()
        backup_codes_str = ",".join(backup_codes)
        
        # Generate QR code
        qr_code_url = generate_qr_code(secret, email)
        
        # Create or update 2FA record
        if existing_2fa:
            existing_2fa.secret_key = secret
            existing_2fa.backup_codes = backup_codes_str
            existing_2fa.method = "totp"
            existing_2fa.verified = False
            session.add(existing_2fa)
        else:
            two_fa = TwoFactorAuth(
                user_id=user_id,
                secret_key=secret,
                backup_codes=backup_codes_str,
                method="totp",
                verified=False,
                is_enabled=False
            )
            session.add(two_fa)
        
        await session.commit()
        
        return Setup2FAResponse(
            secret=secret,
            qr_code_url=qr_code_url,
            backup_codes=backup_codes,
            method="totp"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup 2FA: {str(e)}"
        )


async def verify_totp_code(
    user_id: int,
    code: str,
    session: AsyncSession,
    ip_address: str = None,
    user_agent: str = None
) -> Verify2FAResponse:
    """
    Verify TOTP code for 2FA.
    
    Args:
        user_id: The user ID
        code: 6-digit TOTP code
        session: AsyncSession for database operations
        ip_address: IP address for logging
        user_agent: User agent for logging
    
    Returns:
        Verify2FAResponse with verification status
    """
    try:
        # Get 2FA settings
        two_fa = await get_user_2fa_settings(user_id, session)
        
        if not two_fa or not two_fa.secret_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not set up for this user"
            )
        
        # Verify TOTP code
        totp = pyotp.TOTP(two_fa.secret_key)
        
        # Allow 30 second window (current and previous)
        is_valid = totp.verify(code, valid_window=1)
        
        # Log the attempt
        log_entry = TwoFactorAuthLog(
            user_id=user_id,
            attempt_type="verify",
            success=is_valid,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(log_entry)
        
        if is_valid:
            # Mark as verified if first successful verification
            if not two_fa.verified:
                two_fa.verified = True
                two_fa.is_enabled = True
                session.add(two_fa)
            await session.commit()
            return Verify2FAResponse(verified=True, message="2FA code verified successfully")
        else:
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        f_msg = "Failed to verify 2FA code"
        d_msg=f"{f_msg}: {str(e)}"
        if DEBUG:
            logger.error(d_msg)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA code: {str(e)}"
        )


async def verify_backup_code(
    user_id: int,
    code: str,
    session: AsyncSession,
    ip_address: str = None,
    user_agent: str = None
) -> Verify2FAResponse:
    """
    Verify backup code for 2FA recovery.
    
    Args:
        user_id: The user ID
        code: Backup code
        session: AsyncSession for database operations
        ip_address: IP address for logging
        user_agent: User agent for logging
    
    Returns:
        Verify2FAResponse with verification status
    """
    try:
        two_fa = await get_user_2fa_settings(user_id, session)
        
        if not two_fa or not two_fa.backup_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No backup codes available"
            )
        
        # Get backup codes list
        backup_codes = two_fa.backup_codes.split(",")
        
        if code not in backup_codes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid backup code"
            )
        
        # Remove used backup code
        backup_codes.remove(code)
        two_fa.backup_codes = ",".join(backup_codes)
        session.add(two_fa)
        
        # Log the attempt
        log_entry = TwoFactorAuthLog(
            user_id=user_id,
            attempt_type="verify",
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(log_entry)
        
        await session.commit()
        return Verify2FAResponse(verified=True, message="Backup code verified and consumed")
    
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify backup code: {str(e)}"
        )


async def disable_2fa(
    user: User,
    data: Disable2FARequest,
    session: AsyncSession,
) -> dict:
    """
    Disable 2FA for a user.
    
    Args:
        user_id: The user ID
        password: User's password for confirmation
        session: AsyncSession for database operations
    
    Returns:
        Dictionary with status message
    """
    user_id = user.id
    try:
        pin_or_password_verified = verify_pin_or_password(user, data)
        if not pin_or_password_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid pin or password"
            )
        
        # Get and disable 2FA
        two_fa = await get_user_2fa_settings(user_id, session)
        
        if not two_fa or not two_fa.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled for this user"
            )
        
        two_fa.is_enabled = False
        two_fa.verified = False
        two_fa.secret_key = None
        two_fa.backup_codes = None
        session.add(two_fa)
        
        # Log the attempt
        log_entry = TwoFactorAuthLog(
            user_id=user_id,
            attempt_type="disable",
            success=True,
        )
        session.add(log_entry)
        
        await session.commit()
        
        return {"message": "2FA disabled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}"
        )


async def regenerate_backup_codes(
    user: User,
    data: GenerateBackupCodesRequest,
    session: AsyncSession,
) -> dict:
    """
    Regenerate backup codes for a user.
    
    Args:
        user_id: The user ID
        password: User's password for confirmation
        session: AsyncSession for database operations
    
    Returns:
        Dictionary with new backup codes
    """
    user_id = user.id
    try:
        # Verify password
        pin_or_password_verified = verify_pin_or_password(user, data)
        if not pin_or_password_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid pin or password"
            )
        
        # Get 2FA settings
        two_fa = await get_user_2fa_settings(user_id, session)
        
        if not two_fa or not two_fa.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled for this user"
            )
        
        # Generate new backup codes
        new_backup_codes = generate_backup_codes()
        two_fa.backup_codes = ",".join(new_backup_codes)
        session.add(two_fa)
        
        await session.commit()
        
        return {
            "message": "Backup codes regenerated successfully",
            "backup_codes": new_backup_codes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate backup codes: {str(e)}"
        )


async def get_2fa_status(
    user_id: int,
    session: AsyncSession
) -> TwoFactorAuthSchema:
    """
    Get the 2FA status for a user.
    
    Args:
        user_id: The user ID
        session: AsyncSession for database operations
    
    Returns:
        TwoFactorAuthSchema with user's 2FA settings
    """
    try:
        two_fa = await get_user_2fa_settings(user_id, session)
        
        if not two_fa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA settings not found for this user"
            )
        
        return two_fa
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve 2FA status: {str(e)}"
        )
