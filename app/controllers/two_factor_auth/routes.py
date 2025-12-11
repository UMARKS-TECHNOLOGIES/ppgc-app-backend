"""
Two-factor authentication routes.
"""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.models import User
from ppgc_backend.app.controllers.auth.services import decode_user_from_token
from ppgc_backend.app.controllers.two_factor_auth.schemas import (
    Enable2FARequest,
    Setup2FAResponse,
    Verify2FARequest,
    Verify2FAResponse,
    TwoFactorAuthSchema,
    Disable2FARequest,
    GenerateBackupCodesRequest,
)
from ppgc_backend.app.controllers.two_factor_auth.services import (
    setup_totp_2fa,
    verify_totp_code,
    verify_backup_code,
    disable_2fa,
    regenerate_backup_codes,
    get_2fa_status,
)

router = APIRouter(prefix="/2fa", tags=["two-factor-auth"])


@router.post("/setup/", response_model=Setup2FAResponse, status_code=status.HTTP_201_CREATED)
async def setup_2fa(
    setup_request: Enable2FARequest,
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Set up two-factor authentication (TOTP) for the user.
    
    Args:
        setup_request: Setup request with method type
        current_user: The authenticated user
        session: Database session
    
    Returns:
        Setup2FAResponse with secret, QR code, and backup codes
    """
    if setup_request.method != "totp":
        raise ValueError("Only TOTP method is currently supported")
    
    return await setup_totp_2fa(
        user_id=current_user.id,
        session=session,
        email=current_user.email
    )


@router.post("/verify/", response_model=Verify2FAResponse, status_code=status.HTTP_200_OK)
async def verify_2fa(
    verify_request: Verify2FARequest,
    request: Request,
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Verify 2FA code (TOTP).
    
    Args:
        verify_request: Verify request with 6-digit code
        request: HTTP request for extracting IP and user agent
        current_user: The authenticated user
        session: Database session
    
    Returns:
        Verify2FAResponse with verification status
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await verify_totp_code(
        user_id=current_user.id,
        code=verify_request.code,
        session=session,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.post("/verify-backup/", response_model=Verify2FAResponse, status_code=status.HTTP_200_OK)
async def verify_backup_code_endpoint(
    verify_request: Verify2FARequest,
    request: Request,
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Verify backup code for 2FA recovery.
    
    Args:
        verify_request: Verify request with backup code
        request: HTTP request for extracting IP and user agent
        current_user: The authenticated user
        session: Database session
    
    Returns:
        Verify2FAResponse with verification status
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await verify_backup_code(
        user_id=current_user.id,
        code=verify_request.code,
        session=session,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.get("/status/", response_model=TwoFactorAuthSchema, status_code=status.HTTP_200_OK)
async def get_status(
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Get the current 2FA status for the user.
    
    Args:
        current_user: The authenticated user
        session: Database session
    
    Returns:
        TwoFactorAuthSchema with current 2FA settings
    """
    return await get_2fa_status(
        user_id=current_user.id,
        session=session
    )


@router.post("/disable/", status_code=status.HTTP_200_OK)
async def disable_2fa_endpoint(
    disable_request: Disable2FARequest,
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Disable two-factor authentication for the user.
    Requires password confirmation for security.
    
    Args:
        disable_request: Disable request with password
        current_user: The authenticated user
        session: Database session
    
    Returns:
        Dictionary with status message
    """
    return await disable_2fa(
        user=current_user,
        data=disable_request,
        session=session
    )


@router.post("/regenerate-backup-codes/", status_code=status.HTTP_200_OK)
async def regenerate_backup_codes_endpoint(
    regenerate_request: GenerateBackupCodesRequest,
    current_user: User = Depends(decode_user_from_token),
    session: AsyncSession = Depends(get_db)
):
    """
    Regenerate backup codes for 2FA recovery.
    Requires password confirmation for security.
    
    Args:
        regenerate_request: Regenerate request with password
        current_user: The authenticated user
        session: Database session
    
    Returns:
        Dictionary with new backup codes
    """
    return await regenerate_backup_codes(
        user=current_user,
        data=regenerate_request,
        session=session
    )
