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
from ppgc_backend.app.controllers.auth.services import create_user
from ppgc_backend.app.models import User, TransientVerificationStore
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema


async def create_test_user(
    db: AsyncSession,
    user_data = UserRegistrationSchema(
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="John",
        last_name="Doe",
    )
):
    return await create_user(db, user_data)


@pytest.mark.asyncio
async def test_send_and_confirm_email_verification_code(client_fixture):
    # Unpack the fixture
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    email = "wisdomscott98@gmail.com"
    fullname = "crank gig"

    send_code_data = {
        "email": email,
        "fullname": fullname,
    }

    # 1️⃣ Send verification code
    response = await httpx_client.post(
        "/auth/request-email-verification-code",
        json=send_code_data
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "expiry" in json_response
    assert "detail" in json_response

    # 2️⃣ Check that it's stored in the DB
    stmt = await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == email
        )
    )
    record = stmt.scalars().first()
    assert record is not None
    assert record.email_code_expiry_time is not None

    # Save the code for use in confirmation
    code = record.email_code
    assert code and isinstance(code, str)

    # 3️⃣ Try resending before expiry (should return 302)
    response = await httpx_client.post(
        "/auth/request-email-verification-code",
        json=send_code_data
    )
    assert response.status_code == 302
    assert response.json()['detail'] == "An email code has already been sent."

    # 4️⃣ Confirm email using the correct code
    confirm_data = {
        "email": email,
        "code": code,
    }
    response = await httpx_client.post(
        "/auth/confirm-email-verification-code",
        json=confirm_data
    )
    assert response.status_code == 200
    assert response.json()['message'] == "The email address has been successfully verified."

    # 5️⃣ Try confirming again (should be gone or invalid)
    response = await httpx_client.post(
        "/auth/confirm-email-verification-code",
        json=confirm_data
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Verification code not found or expired."


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
    await test_db.flush()

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

    # 3️⃣ Check it's gone
    await test_db.refresh(transient_instance)
    assert not transient_instance

    # 4️⃣ Confirm again — should now 404
    response = await httpx_client.post(
        "/auth/confirm-email-verification-code",
        json=confirm_data
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Verification code not found or expired."


@pytest.mark.asyncio
async def test_expired_verification_code_cleanup(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    test_user = await create_test_user(test_db)

    email = "cleanup@example.com"
    fullname = "Cleanup Bot"
    send_code_data = {
        "email": email,
        "fullname": fullname,
    }

    # Request verification code
    response = await httpx_client.post(
        "/auth/request-email-verification-code",
        json=send_code_data
    )
    assert response.status_code == 200

    # Manually expire the code for the test
    stmt = await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == email
        )
    )
    record = stmt.scalars().first()
    assert record

    # Simulate expiration
    record.email_code_expiry_time = datetime.utcnow()  # already expired
    test_db.add(record)
    await test_db.commit()

    # Wait enough time for the cleanup task to run (based on task interval + buffer)
    await asyncio.sleep(35 * 60)  # Assuming task sleeps for 30 mins after expiry

    # Ensure the code is removed
    stmt = await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == email
        )
    )
    cleaned_record = stmt.scalars().first()
    assert cleaned_record is None
