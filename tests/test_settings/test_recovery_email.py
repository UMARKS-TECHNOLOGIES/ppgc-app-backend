import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth import signin_for_access_token
from ppgc_backend.config.settings import REAL_TEST_EMAIL
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user, user_data

@pytest.mark.asyncio
async def test_request_recovery_email_change_success(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    access_token = await signin_for_access_token(user_data, httpx_client)
    headers = {"Authorization": f"Bearer {access_token}"}

    #=============================
    # Test Request
    #=============================
    new_email = REAL_TEST_EMAIL
    response = await httpx_client.post(
        "/settings/recovery-email/request/",
        json={"recovery_email": new_email},
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "expiry" in json_response
    assert "detail" in json_response

    # Check DB for transient record
    stmt = await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == new_email
        )
    )
    record = stmt.scalars().first()
    assert record is not None
    assert record.reason == "recovery-email-verification"
    code = record.email_code
    assert code is not None
    assert record.email_code_expiry_time is not None


    #=============================
    # Test Confirmation
    #=============================
    confirm_payload = {"email": new_email, "code": code}
    confirm_resp = await httpx_client.post(
        "/settings/recovery-email/confirm/",
        json=confirm_payload,
        headers=headers
    )

    assert confirm_resp.status_code == 200
    json_response = confirm_resp.json()
    assert json_response['verified'] is True
    assert json_response['recovery_email'] == new_email

    # verify user updated in DB
    updated_user = (await test_db.execute(
        select(User).where(User.id == user.id)
    )).scalars().first()
    assert updated_user.recovery_email == new_email
    assert updated_user.recovery_email_verified is True

    # transient should be deleted by decorator
    after = (await test_db.execute(
        select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == new_email
        )
    )).scalars().first()
    assert after is None