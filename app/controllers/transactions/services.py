from sqlalchemy.ext.asyncio import AsyncSession

from .models import Transaction
from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from ppgc_backend.log_config.logger_config import log_error

async def create_transaction(db: AsyncSession, trx_data: dict, user_id: int):
    try:
        trx = Transaction(
            **trx_data,
            user_id = user_id,
        )
        
        db.add(trx)
        await db.commit()
        await db.refresh(trx)
        return trx
    except Exception as e:
        f_msg = "An error occured while creating transaction."
        d_msg = f"{f_msg} Reason: {e}"
        if DEBUG:
            logger.info(d_msg)
        log_error(d_msg)
        raise e