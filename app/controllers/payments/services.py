import httpx 
import hashlib
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.config import settings
from .schemas import PaymentRequestSchema
from ppgc_backend.app.initiator import logger
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.transactions.enums import TRXType
from ppgc_backend.app.controllers.activity_logging.services import log_activity
from ppgc_backend.app.controllers.transactions.services import create_transaction

async def create_rrr(db: AsyncSession, data: PaymentRequestSchema, user: User, amount: float, name: str, email: str | None = None, phone: str | None = None) -> dict[str, Any]:
    url = f"{settings.REMITA_BASE_URL.rstrip('/')}{settings.REMITA_RRR_PATH}"
    payload = {
        "amount": data.amount,
        "payerName": data.name,
        "payerEmail": data.email,
        "payerPhone": data.phone,
    }
    if settings.REMITA_MERCHANT_ID:
        payload.update({"merchantId": settings.REMITA_MERCHANT_ID})
    if settings.REMITA_SERVICE_TYPE_ID:
        payload.update({"serviceTypeId": settings.REMITA_SERVICE_TYPE_ID})

    headers = {"Content-Type": "application/json"}
    if settings.REMITA_API_KEY and settings.REMITA_USE_BEARER:
        headers["Authorization"] = f"Bearer {settings.REMITA_API_KEY}"

    remita_resp = None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        remita_resp = resp.json()

    rrr = (
        remita_resp.get('RRR')
        or remita_resp.get('rrr')
        or (remita_resp.get('data') or {}).get('RRR')
        or (remita_resp.get('data') or {}).get('rrr')
    )

    trx_payload = {
        'amount': data.amount,
        'name': data.name,
        'trx_type': TRXType.deposit,
        'trx_id': rrr or '',
    }

    trx = await create_transaction(db, trx_payload, user.id)

    await log_activity(db, user, action='create_rrr', description=str(remita_resp))

    return {'remita': remita_resp, 'transaction': {'id': trx.id, 'trx_id': trx.trx_id}}


async def verify_rrr(rrr: str, amount: float | None = None) -> dict[str, Any]:
    base = settings.REMITA_BASE_URL.rstrip('/')
    path = settings.REMITA_VERIFY_PATH.rstrip('/')
    url = f"{base}{path}/{rrr}"
    if settings.REMITA_MERCHANT_ID:
        url = f"{url}/{settings.REMITA_MERCHANT_ID}"
    if settings.REMITA_SERVICE_TYPE_ID:
        url = f"{url}/{settings.REMITA_SERVICE_TYPE_ID}"
    if amount is not None:
        url = f"{url}/{amount}"

    headers = {}
    if settings.REMITA_API_KEY and settings.REMITA_USE_BEARER:
        headers["Authorization"] = f"Bearer {settings.REMITA_API_KEY}"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def compute_hash(*parts: str) -> str:
    s = "".join(parts)
    return hashlib.sha512(s.encode()).hexdigest()
