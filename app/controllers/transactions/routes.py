from sqlalchemy.future import select
from fastapi import (
    Body,
    status,
    Depends, 
    APIRouter, 
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Transaction
from .services import create_transaction
from ppgc_backend.app.database import get_db
from .schemas import DepositSchema, WithdrawSchema
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import decode_user_from_token


router = APIRouter(prefix='/trx')

@router.post('/deposit/')
async def deposit_endpoint(
    data: DepositSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    return await create_transaction(db, data.model_dump(), user.id)


@router.post('/withdraw/')
async def deposit_endpoint(
    data: WithdrawSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token)
):
    trx = (await db.execute(
        select(Transaction)
        .where(Transaction.trx_id == data.trx_id)
    )).scalars().first()
    if trx:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail="Duplicate trx_id."
        )
    
    return await create_transaction(db, data.model_dump(), user.id)