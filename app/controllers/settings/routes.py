from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from .services import (
    get_user_settings,
    create_or_update_pass_code,
    handle_update_user_settings,
    update_notification_settings,
    confirm_recovery_email_change,
    request_recovery_email_change,
)
from .schemas import (
    RecoveryEmailRequestSchema,
    RecoveryEmailVerificationSchema,
    RecoveryEmailResponseSchema,
    UserSettingsResponseSchema,
    UserSettingsSchema,
)
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.schemas import PasscodeSchema
from ppgc_backend.app.controllers.auth.services import decode_user_from_token

router = APIRouter(prefix='/settings')


@router.post("/update-passcode/")
async def update_passcode_endpoint(
    data: PasscodeSchema = Body(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    return await create_or_update_pass_code(
        db=session,
        user=user,
        pass_code=data.pass_code
    )


@router.post("/recovery-email/change-authorization/", response_model=RecoveryEmailResponseSchema, status_code=200)
async def request_recovery_email_endpoint(
    data: RecoveryEmailRequestSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """
    Request a recovery email change by sending a verification code to the new email.
    
    Returns:
        - detail: Message confirming code was sent
        - expiry: ISO format timestamp when code expires
    """
    return await request_recovery_email_change(db,user,data.recovery_email)


@router.post("/recovery-email/change-confirmation/", response_model=RecoveryEmailResponseSchema, status_code=200)
async def confirm_recovery_email_endpoint(
    data: RecoveryEmailVerificationSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """
    Confirm recovery email change with verification code.
    
    Requires:
        - verification_code: 4-digit code sent to the recovery email
        
    Returns:
        - detail: Success message
        - recovery_email: The confirmed recovery email
        - verified: True if successful
    """
    return await confirm_recovery_email_change(data, db, user)


@router.get("/", response_model=UserSettingsResponseSchema, status_code=200)
async def get_settings_endpoint(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """
    Get current user settings including email, recovery email, and notification preferences.
    """
    return await get_user_settings(db=session, user=user)


@router.patch("/", response_model=UserSettingsResponseSchema, status_code=200)
async def update_user_settings(
    data: UserSettingsSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """
    Get current user settings including email, recovery email, and notification preferences.
    """
    return await handle_update_user_settings(data.model_dump(exclude_none=True), db, user)