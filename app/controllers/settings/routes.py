from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from .services import create_or_update_pass_code
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