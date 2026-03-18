from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BankAccount
from .schemas import BankAccResp, BankAccCreate, BankAccPatch
from .services import (
    create_acc,
    list_user_accs,
    update_acc,
    delete_acc,
)
from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.utils import require_owner_dep
from ppgc_backend.app.controllers.auth.services import decode_user_from_token

router = APIRouter(prefix="/bank-accounts", tags=['bank-accounts'])


@router.post('/', response_model=BankAccResp, status_code=201)
async def create_bank_acc(
    payload: BankAccCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """Create a bank account attached to the authenticated user."""
    return await create_acc(db, user.id, payload)


@router.get('/', response_model=list[BankAccResp])
async def list_bank_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """List bank accounts belonging to the authenticated user."""
    return await list_user_accs(db, user.id)


@router.get('/{id}/', response_model=BankAccResp)
async def fetch_bank_account(
    instance: BankAccount = Depends(require_owner_dep(BankAccount)),
):
    """Fetch a single bank account. Only owner may fetch."""
    return instance


@router.patch('/{id}/', response_model=BankAccResp)
async def patch_bank_account(
    id: int,
    payload: BankAccPatch,
    db: AsyncSession = Depends(get_db),
    instance: BankAccount = Depends(require_owner_dep(BankAccount)),
):
    """Update a bank account. Only owner may update."""
    return await update_acc(db, id, instance, payload.model_dump(exclude_none=True))


@router.delete('/{id}/', status_code=204)
async def remove_bank_account(
    id: int,
    db: AsyncSession = Depends(get_db),
    instance: BankAccount = Depends(require_owner_dep(BankAccount)),
):
    """Delete a bank account. Only owner may delete."""
    await delete_acc(db, id, instance)