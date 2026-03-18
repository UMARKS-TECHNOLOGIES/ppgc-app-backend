import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from ppgc_backend.config.settings import (
    SUPER_ADMIN_PASSWORD,
)
from ppgc_backend.tests.auth import signin_for_access_token
from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.models import TransientVerificationStore
from ppgc_backend.tests.auth.test_user_creation import UserRegistrationSchema
from ppgc_backend.app.controllers.auth.services import get_password_reset_ttl
from ppgc_backend.app.controllers.auth.schemas import VerifyEmailAndSignUserUpSchema
from ppgc_backend.app.controllers.auth.services import initialize_admin, validate_role_token


@pytest.mark.asyncio
async def test_generate_staff_link(client_fixture):
    """Test generating link"""
    httpx_client: AsyncClient = client_fixture['http_client']
    test_db: AsyncSession = client_fixture['db']

    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=admin.email,
        first_name="Admin"
    )
    access_token = await signin_for_access_token(admin_user_data, httpx_client)
    headers = {'Authorization': f'Bearer {access_token}'}

    payload = {}
    resp = await httpx_client.post(
        '/auth/generate-staff-invite-token/', 
        json=payload, 
        headers=headers
    )
    assert resp.status_code == 201
    token = resp.json()['token']
    assert isinstance(token,str)

    #================================
    # create transient instance
    #================================
    dummy_code = "1234"
    dummy_email = "1234@gmail.com"
    verification_instance = TransientVerificationStore(
        email_address = dummy_email,
        reason = EmailManagementReasonChoice.email_verification,
        email_code=dummy_code,
        email_code_expiry_time=datetime.now(timezone.utc) + timedelta(seconds=get_password_reset_ttl()),
    )
    test_db.add(verification_instance)
    await test_db.commit()

    #=============================
    # make confirmation request
    #=============================
    payload = {    
        "code": dummy_code,
        "role_token": token,
        "email": dummy_email,
        "first_name": "Jacob",
        "pin": "whatchamcallit"
    }
    response = await httpx_client.post(
        '/auth/confirm-email-verification-code/',
        json=payload
    )
    assert response.status_code == 200

    #=============================
    # Make signin request
    #=============================
    response = await httpx_client.post(
        '/auth/signin/',
        json={"email": dummy_email, "pin": payload['pin']}
    )
    assert response.status_code == 200