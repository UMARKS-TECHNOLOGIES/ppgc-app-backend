import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from ppgc_backend.app.utils.store import (
    email_verification_code_ttl,
)
from ppgc_backend.app.models import User, TransientVerificationStore
from ppgc_backend.app.controllers.auth.services import verify_password


@pytest.mark.asyncio
async def test_verify_email_code_and_signup(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj['db']
        httpx_client: AsyncClient = fixture_obj['http_client']
        break

    # 1️⃣ Insert dummy verification record
    dummy_code = "1234"
    dummy_email = 'joe@gmail.com'
    test_pin = '123456'
    test_name = 'Joe cole'

    transient_instance = TransientVerificationStore(
        email_address=dummy_email,
        email_code=dummy_code,
        email_code_expiry_time=datetime.now(timezone.utc) + timedelta(seconds=email_verification_code_ttl())
    )
    test_db.add(transient_instance)
    await test_db.commit()

    confirm_data = {
        "email": dummy_email,
        "code": dummy_code,
        "fullname": test_name,
        "pin": test_pin,

    }

    # 2️⃣ Confirm it — should succeed
    response = await httpx_client.post(
        "/auth/confirm-email-verification-code",
        json=confirm_data
    )
    assert response.status_code == 200
    assert response.json()['detail'] == "Email verified and user registered."


    # 4️⃣ Confirm again — should now 404
    response = await httpx_client.post(
        "/auth/confirm-email-verification-code",
        json=confirm_data
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Verification code incorrect or expired."

    # assert that the user exists
    query = await test_db.execute(
        select(User)
        .where(
            User.email == dummy_email
    ))
    user: User = query.scalars().one()
    assert verify_password(confirm_data['pin'],user.pin_hash)
    split_names = test_name.split()
    assert user.first_name == split_names[0]
    assert user.last_name == split_names[1]