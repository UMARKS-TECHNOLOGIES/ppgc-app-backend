from functools import wraps
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Path, Depends
from ppgc_backend.app.controllers.auth.services import decode_user_from_token


from .models import Investment
from .tools import compute_roi
from .enums import InvestmentStatus
from .schemas import InvestmentCreate
from ppgc_backend.app.database import get_db
from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.log_config.logger_config import log_error
from ppgc_backend.app.controllers.transactions.models import Transaction

INVESTMENTNOTFOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment instance does not exist.")

async def require_owner(
    investment_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    requester: User = Depends(decode_user_from_token),
):
    investment = await db.get(Investment,investment_id)
    if not investment:
        raise INVESTMENTNOTFOUND

    if investment.user_id != requester.id:
        detail = "You do not have permission to perform this action"
        if DEBUG:
            logger.error(detail)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    return requester  # Optionally return for access


# def require_owner(func):
#     @wraps(func)
#     async def wrapper(db: AsyncSession, user_id: int, investment_id: int, *args, **kwargs):
#         return func(db, user_id, investment_id, *args, **kwargs)
#     return wrapper


async def create_investment(db: AsyncSession, user_id: int, investment_data: InvestmentCreate):
    try:
        new_investment = Investment(
            user_id=user_id, 
            **investment_data.model_dump(exclude=['trx']),
            trx = Transaction(
                **investment_data.trx.model_dump(),
                user_id = user_id,
            ),
        )
        db.add(new_investment)
        await db.commit()
        await db.refresh(new_investment)
        return new_investment
    except Exception as e:
        f_msg = "An error occured while creating investment."
        d_msg = f"{f_msg} Reason: {e}"
        if DEBUG:
            logger.info(d_msg)
        log_error(d_msg)
        raise e

async def get_user_investment(db: AsyncSession, user_id:int, investment_id: int):
    query = await db.execute(
        select(Investment)
        .where(
            Investment.id == investment_id,
            Investment.user_id == user_id
        )
    )
    investment = query.scalars().first()

    if not investment:
        raise INVESTMENTNOTFOUND
    
    return investment


async def get_user_investments(db: AsyncSession, user_id: int):
    investments = (await db.execute(
        select(Investment)
        .where(Investment.user_id == user_id)
    )).scalars().all()
    return investments


async def update_investment_status(
    db: AsyncSession,
    investment_id: int,
    u_status: InvestmentStatus,
):
    
    investment = await db.get(Investment, investment_id)
    
    # update status
    investment.status = u_status
    db.add(investment)
    await db.commit()
    await db.refresh(investment)
    return investment


async def delete_investment(
    db: AsyncSession,
    investment_id: int,
):
    investment = await db.get(Investment, investment_id)
    await db.delete(investment)
    await db.commit()
