from functools import wraps
from fastapi import Request
from sqlalchemy import and_
from sqlalchemy.future import select
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Request

from .schemas import EmailEtCodeSchema
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.app.enums import EmailManagementReasonChoice as TransientReason

def is_secure_request(request: Request) -> bool:
    return request.url.scheme == "https"

# decorator
def confirm_email_verification_code(reason: TransientReason = None):
    def outer_wrapper(func):
        @wraps(func)
        async def wrapper(
            data: EmailEtCodeSchema,
            session: AsyncSession,
            *args,
            **kwargs
        ):
            filters = [
                TransientVerificationStore.email_address == data.email,
                TransientVerificationStore.email_code == data.code,
            ]

            # If reason is provided, enforce it
            if reason is not None:
                filters.append(TransientVerificationStore.reason == reason)


            record = (await session.execute(
                select(TransientVerificationStore).where(and_(*filters))
            )).scalars().first()

            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Code incorrect or expired."
                )

            try:
                # Expiry check (recommended)
                now = datetime.now(timezone.utc)
                if record.email_code_expiry_time and record.email_code_expiry_time <= now:
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE,
                        detail="Code expired."
                    )
                return await func(data, session, *args, **kwargs)
            finally:
                await session.delete(record)
                await session.commit()
        return wrapper
    return outer_wrapper

async def request_verification_code(email_address:str, username: str) -> str:
    pass