import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.tests.auth.test_user_creation import create_test_user

@pytest.mark.asyncio
async def test_send_password_reset_mail(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create a user whose email will be used for password reset
    user = await create_test_user(test_db)
    user.email = 'crankgig@gmail.com'
    test_db.add(user)
    await test_db.commit()

    email = user.email

    #** Call the password reset endpoint **#
    response = await httpx_client.post(
        "/auth/send-password-reset-mail",
        json={"email": email}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'detail' in data
    assert 'expiry' in data

    #** Call endpoint again before expiry **#
    response = await httpx_client.post(
        "/auth/send-password-reset-mail",
        json={"email": email}
    )
    assert response.status_code == 302

    # fetch transient instance
    reason = EmailManagementReasonChoice.password_change.value
    query = await test_db.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == email,
            TransientVerificationStore.reason == reason
        )
    )
    reset_instance = query.scalars().first()
    assert reset_instance
    

    #** Call endpoint again before expiry **#
    new_password = '$whathaFak'
    response = await httpx_client.post(
        "/auth/change-pin-or-password",
        json={
            "email": email,
            "code": reset_instance.email_code,
            "password": new_password
        }
    )
    assert response.status_code == 200

    expiry_time = reset_instance.email_code_expiry_time
    now = datetime.now(timezone.utc)
    remaining_time: timedelta = expiry_time-now
    await asyncio.sleep(remaining_time.total_seconds()+2)
    await test_db.refresh(reset_instance)
    assert not reset_instance.email_code_expiry_time