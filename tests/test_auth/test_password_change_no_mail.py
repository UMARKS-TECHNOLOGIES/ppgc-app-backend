import pytest
import secrets
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.config.settings import REAL_TEST_EMAIL
from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import get_password_reset_ttl

@pytest.mark.asyncio
async def test_password_change_no_mail(client_fixture):
    test_db: AsyncSession = client_fixture["db"]
    httpx_client: AsyncClient = client_fixture["http_client"]

    # Create a user whose email will be used for password reset
    user = await create_test_user(test_db)
    email = REAL_TEST_EMAIL
    user.email = email
    test_db.add(user)
    await test_db.commit()

    code = "1234"
    # create transient instance
    reason = EmailManagementReasonChoice.password_change
    reset_instance = TransientVerificationStore(
        email_address = email,
        reason = reason,
        email_code = code,
        email_code_expiry_time = datetime.now(timezone.utc) + timedelta(seconds=get_password_reset_ttl()),
    )
    test_db.add(reset_instance)
    await test_db.commit()

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
    

    #** Call endpoint again before expiry **#
    new_password = '$whathaFak'
    response = await httpx_client.post(
        "/auth/change-pin-or-password/",
        json={
            "email": email,
            "password": new_password
        }
    )
    assert response.status_code == 200
