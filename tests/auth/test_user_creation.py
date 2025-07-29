import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


from ppgc_backend.app.models import User, TransientVerificationStore
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema
from ppgc_backend.app.controllers.auth.services import (
    create_user, 
    verify_password,
)


async def create_test_user(
    db: AsyncSession,
    user_data = UserRegistrationSchema(
        email="test@example.com",
        pin="password123",
        first_name="John",
        last_name="Doe",
    )
):
    return await create_user(db, user_data)


@pytest.mark.asyncio
async def test_request_and_verify_email_verification_code(client_fixture):
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
    json_response = response.json()
    assert json_response['detail']['status'] == "An email code has already been sent."
    assert json_response['detail']['status']

    # retrieve code
    query = await test_db.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == email,
    ))
    instance = query.scalars().one()
    code = instance.email_code
    

    confirm_data = {
        "email": email,
        "code": code,
        "fullname": fullname,
        "pin": "test_pin",

    }
    # Confirm it — should succeed
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
            User.email == email
    ))
    user: User = query.scalars().one()
    assert verify_password(confirm_data['pin'],user.pin_hash)
    split_names = fullname.split()
    assert user.first_name == split_names[0]
    assert user.last_name == split_names[1]