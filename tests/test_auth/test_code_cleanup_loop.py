import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from ppgc_backend.app.utils.store import (
    email_verification_code_ttl,
)
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.app.controllers.auth.services import email_code_cleanup_loop
from ppgc_backend.app.enums import EmailManagementReasonChoice as TransientReason  



@pytest.mark.asyncio
async def test_email_code_cleanup_loop(client_fixture):
    test_db: AsyncSession = client_fixture['db']

    # 1️⃣ Insert dummy verification record
    dummy_code = "1234"
    dummy_email = 'joe@gmail.com'

    reason = TransientReason.email_verification
    transient_instance = TransientVerificationStore(
        email_address=dummy_email,
        email_code=dummy_code,
        email_code_expiry_time=datetime.now(timezone.utc) + timedelta(seconds=email_verification_code_ttl()),
        reason = reason
    )
    test_db.add(transient_instance)
    await test_db.commit()
    await email_code_cleanup_loop(
        dummy_email, dummy_code, reason,
    )
    
    # allow to sleep for expiry seconds + 2
    await asyncio.sleep(email_verification_code_ttl()+2)

    # assert non-existence    
    query = await test_db.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == dummy_email,
            TransientVerificationStore.email_code == dummy_code,
        ))
    assert not query.scalars().first()
