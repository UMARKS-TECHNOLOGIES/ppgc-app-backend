"""
Recovery email settings management
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from .schemas import RecoveryEmailVerificationSchema
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.app.controllers.auth.services import (
    email_code_cleanup_loop,
    request_verification_code,
    handle_email_code_request,
)
from ppgc_backend.app.utils.store import (
    email_verification_code_ttl,
)
from ppgc_backend.app.controllers.auth.services import confirm_email_verification_code


async def create_or_update_pass_code(db: AsyncSession, user: User, pass_code: str):
    user.pass_code = pass_code
    db.add(user)
    await db.commit()


async def request_recovery_email_change(
    db: AsyncSession,
    user: User,
    new_recovery_email: str
) -> dict:
    """
    Request a recovery email change by sending a verification code to the new email.
    
    Args:
        db: AsyncSession for database operations
        user: The authenticated user
        new_recovery_email: The new recovery email address to set
        
    Returns:
        dict with detail message and expiry time
    """
    #=====================================================
    # Check if recovery email already set to this address
    #=====================================================
    if user.recovery_email == new_recovery_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recovery email is already set to this address"
        )

    #=====================================================
    # Check if email is already used as primary or recovery by another user
    #=====================================================
    email_check = await db.execute(
        select(User).where(User.email == new_recovery_email)
    )
    if email_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already in use as a primary email"
        )
    recovery_check = await db.execute(
        select(User).where(User.recovery_email == new_recovery_email)
    )
    if recovery_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already in use as a recovery email"
        )
        
    expiry_time = await handle_email_code_request("recovery-email-verification",db,new_recovery_email,user.first_name)

    return {
        "detail": f"Verification code sent to {new_recovery_email}. Please check your email.",
        "expiry": expiry_time.isoformat()
    }


@confirm_email_verification_code
async def confirm_recovery_email_change(
    data: RecoveryEmailVerificationSchema,
    db: AsyncSession,
    user: User,
) -> dict:
    """
    Confirm recovery email change by verifying the code.
    
    Args:
        db: AsyncSession for database operations
        user: The authenticated user
        new_recovery_email: The recovery email to verify
        verification_code: The verification code sent to the email
        
    Returns:
        dict with success message and recovery email
    """
    recovery_email = data.email
    try:
        # Update user's recovery email
        user.recovery_email = recovery_email
        user.recovery_email_verified = True
        db.add(user)
        await db.commit()

        return {
            "detail": "Recovery email verified and set successfully",
            "recovery_email": recovery_email,
            "verified": True
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating recovery email: {str(e)}"
        )


async def get_user_settings(db: AsyncSession, user: User) -> dict:
    """
    Get current user settings.
    
    Args:
        db: AsyncSession for database operations
        user: The authenticated user
        
    Returns:
        dict with user settings
    """
    return {
        "email": user.email,
        "recovery_email": user.recovery_email,
        "recovery_email_verified": user.recovery_email_verified if hasattr(user, 'recovery_email_verified') else False,
        "email_notification": user.email_notification,
        "push_notification": user.push_notification,
        "pass_code": "****" if user.pass_code else None
    }


async def update_notification_settings(
    db: AsyncSession,
    user: User,
    email_notification: bool = None,
    push_notification: bool = None
) -> dict:
    """
    Update notification preferences.
    
    Args:
        db: AsyncSession for database operations
        user: The authenticated user
        email_notification: Whether to receive email notifications
        push_notification: Whether to receive push notifications
        
    Returns:
        dict with updated settings
    """
    if email_notification is not None:
        user.email_notification = email_notification
    
    if push_notification is not None:
        user.push_notification = push_notification

    db.add(user)
    await db.commit()

    return {
        "detail": "Notification settings updated",
        "email_notification": user.email_notification,
        "push_notification": user.push_notification
    }