import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.config.settings import REAL_TEST_EMAIL
from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.tests.test_auth.test_user_creation import create_test_user

@pytest.mark.asyncio
async def test_change_pin_or_password(client_fixture):
    test_db: AsyncSession = client_fixture["db"]
    httpx_client: AsyncClient = client_fixture["http_client"]

    # Create a user whose email will be used for password reset
    user = await create_test_user(test_db)
    email = REAL_TEST_EMAIL
    user.email = email
    test_db.add(user)
    await test_db.commit()


    #** Call the password reset endpoint **#
    response = await httpx_client.post(
        "/auth/send-password-reset-mail/",
        json={"email": email}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'expiry' in data

    #** Call endpoint again before expiry **#
    response = await httpx_client.post(
        "/auth/send-password-reset-mail/",
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
    

    #** Confirm reset code before changing password **#
    response = await httpx_client.post(
        "/auth/confirm-pin-or-password-change-code/",
        json={
            "email": email,
            "code": reset_instance.email_code,
        }
    )
    assert response.status_code == 200
    confirmation_data = response.json()
    assert "x_expiration" in confirmation_data

    #** Change password after successful confirmation **#
    new_password = '$whathaFak'
    response = await httpx_client.post(
        "/auth/change-pin-or-password/",
        json={
            "email": email,
            "password": new_password
        }
    )
    assert response.status_code == 200

    # now = datetime.now(timezone.utc)
    # remaining_time: timedelta = expiry_time-now
    # await asyncio.sleep(remaining_time.total_seconds()+2)
    # await test_db.refresh(reset_instance)
    # assert not reset_instance.email_code_expiry_time
