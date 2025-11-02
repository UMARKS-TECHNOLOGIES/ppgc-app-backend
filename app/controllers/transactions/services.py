from sqlalchemy.ext.asyncio import AsyncSession

from .models import Transaction

async def create_transaction(db: AsyncSession, trx_data: dict):
    # Add transaction record
    trx = Transaction(
        **trx_data
    )
    
    db.add(trx)
    await db.commit()
    await db.refresh(trx)
    return trx