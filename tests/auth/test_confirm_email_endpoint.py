import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from ppgc_backend.config.settings import REAL_TEST_EMAIL
from ppgc_backend.app.models import User, TransientVerificationStore
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema
from ppgc_backend.app.controllers.auth.services import (
    create_user, 
    verify_password,
    get_password_hash,
)
from ppgc_backend.app.utils.store import email_verification_code_ttl


@pytest.mark.asyncio
async def test_confirm_email_verification_code_with_valid_transient_instance(client_fixture):
    """
    Test the /auth/confirm-email-verification-code/ endpoint
    with a pre-created transient verification store instance.
    """
    # Unpack the fixture
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    email = REAL_TEST_EMAIL
    first_name = "test_confirm"
    last_name = "user"
    verification_code = "TEST_CODE_12345"
    pin = "secure_pin_123"

    # ===============================================
    # 1️⃣ Create a transient instance manually
    # ===============================================
    transient_instance = TransientVerificationStore(
        email_address=email,
        email_code=verification_code,
        email_code_expiry_time=datetime.now(timezone.utc) + timedelta(minutes=email_verification_code_ttl()),
        email_address_verified=False,
    )
    test_db.add(transient_instance)
    await test_db.commit()
    await test_db.refresh(transient_instance)
    
    # Verify the transient instance was created
    stmt = await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == email
        )
    )
    created_instance = stmt.scalars().first()
    assert created_instance is not None
    assert created_instance.email_code == verification_code
    assert created_instance.email_address == email

    # ===============================================
    # 2️⃣ Test confirm endpoint with correct code
    # ===============================================
    confirm_data = {
        "email": email,
        "code": verification_code,
        "first_name": first_name,
        "last_name": last_name,
        "pin": pin,
    }

    response = await httpx_client.post(
        "/auth/confirm-email-verification-code/",
        json=confirm_data
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['detail'] == "Email verified and user registered."

    # ===============================================
    # 3️⃣ Verify user was created in database
    # ===============================================
    user_stmt = await test_db.execute(
        select(User).where(User.email == email)
    )
    created_user: User = user_stmt.scalars().first()
    assert created_user is not None
    assert created_user.email == email
    assert created_user.first_name == first_name
    assert created_user.last_name == last_name
    assert verify_password(pin, created_user.pin_hash)

    # ===============================================
    # 4️⃣ Verify transient instance was marked as verified
    # ===============================================
    transient_inst = (await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == email
        )
    )).scalars().first()
    assert not transient_inst