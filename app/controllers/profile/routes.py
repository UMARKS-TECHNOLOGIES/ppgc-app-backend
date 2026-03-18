from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.settings.services import (
    get_user_settings,
    handle_update_user_settings,
)
from ppgc_backend.app.controllers.settings.schemas import (
    UserSettingsResponseSchema,
    UserSettingsSchema,
)
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.schemas import PasscodeSchema
from ppgc_backend.app.controllers.auth.services import decode_user_from_token

router = APIRouter(prefix='/profile')


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