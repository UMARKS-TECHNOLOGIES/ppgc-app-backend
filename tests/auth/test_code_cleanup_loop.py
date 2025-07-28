import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone


from ppgc_backend.app.utils.store import (
    email_verification_code_ttl,
    transient_email_verification_ttl,
)
from ppgc_backend.app.controllers.auth.services import create_user, email_code_cleanup_loop
from ppgc_backend.app.models import User, TransientVerificationStore
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema



@pytest.mark.asyncio
async def test_email_code_cleanup_loop(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # 1️⃣ Insert dummy verification record
    dummy_code = "1234"
    dummy_email = 'joe@gmail.com'

    transient_instance = TransientVerificationStore(
        email_address=dummy_email,
        email_code=dummy_code,
        email_code_expiry_time=datetime.now(timezone.utc) + timedelta(seconds=email_verification_code_ttl())
    )
    test_db.add(transient_instance)
    await test_db.commit()
    await email_code_cleanup_loop(
        test_db, 
        dummy_email, 
        dummy_code, 
    )
    

    # allow to sleep for expiry seconds + 2
    await asyncio.sleep(email_verification_code_ttl()+2)
    await test_db.refresh(transient_instance)
    assert not transient_instance.email_code_expiry_time
    
    # allow to sleep for transient ttl + 2
    await asyncio.sleep(transient_email_verification_ttl()+2)
    query = await test_db.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == dummy_email,
            TransientVerificationStore.email_code == dummy_code,
        ))
    assert not query.scalars().first()
