from sqlalchemy.ext.asyncio import AsyncSession

from .models import BankAccount
from .schemas import BankAccCreate
from fastapi import HTTPException, status
from sqlalchemy.future import select
from ppgc_backend.app.initiator import logger


async def create_acc(db: AsyncSession, user_id: int, data: BankAccCreate):
    instance = BankAccount(
        **data.model_dump(),
        user_id = user_id
    )
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance


async def get_acc(db: AsyncSession, acc_id: int) -> BankAccount:
    try:
        instance = await db.get(BankAccount, acc_id)
        if not instance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
        return instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bank account {acc_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch bank account")


async def list_user_accs(db: AsyncSession, user_id: int) -> list[BankAccount]:
    try:
        result = await db.execute(select(BankAccount).where(BankAccount.user_id == user_id).order_by(BankAccount.id.desc()))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing bank accounts for user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list bank accounts")


async def update_acc(db: AsyncSession, acc_id: int, instance: BankAccount, data: dict) -> BankAccount:
    try:
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating bank account {acc_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update bank account")


async def delete_acc(db: AsyncSession, acc_id: int, instance: BankAccount) -> None:
    try:
        await db.delete(instance)
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting bank account {acc_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete bank account")