from fastapi import APIRouter, Depends, Body, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .schemas import PaymentRequestSchema, WebhookPayload
from .services import handle_create_rrr, verify_rrr
from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.auth.services import decode_user_from_token
from ppgc_backend.app.controllers.transactions.services import create_transaction
from ppgc_backend.app.controllers.transactions.enums import TRXType
from ppgc_backend.app.controllers.transactions.models import Transaction
from ppgc_backend.app.initiator import logger
from ppgc_backend.app.controllers.activity_logging.services import log_activity


router = APIRouter(prefix='/payments')


@router.post('/rrr/', status_code=status.HTTP_201_CREATED)
async def create_rrr_endpoint(
    data: PaymentRequestSchema = Body(...),
    db: AsyncSession = Depends(get_db),
    user = Depends(decode_user_from_token),
):
    return await handle_create_rrr(db, data, user)


@router.post('/webhook/', status_code=status.HTTP_200_OK)
async def remita_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.json()

    logger.info(f"remita webhook received: {payload}")

    rrr = (
        payload.get('RRR')
        or payload.get('rrr')
        or (payload.get('data') or {}).get('RRR')
    )

    if rrr:
        try:
            verify_resp = await verify_rrr(rrr)
            trx = (await db.execute(select(Transaction).where(Transaction.trx_id == rrr))).scalars().first()
            if trx:
                trx.name = trx.name
                db.add(trx)
                await db.commit()
            return {'status': 'ok', 'verify': verify_resp}
        except Exception as e:
            logger.error(f"Error verifying webhook rrr={rrr}: {e}")
            return {'status': 'error', 'detail': str(e)}

    return {'status': 'ignored'}
