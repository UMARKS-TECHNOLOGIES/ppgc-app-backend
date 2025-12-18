import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.config.settings import (
    SUPER_ADMIN_PASSWORD,
    SUPER_ADMIN_EMAIL_ADDRESS,
)
from ppgc_backend.tests.auth import signin_for_access_token
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from ppgc_backend.app.controllers.auth.schemas import VerifyEmailAndSignUserUpSchema
from ppgc_backend.app.controllers.auth.services import initialize_admin, validate_role_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user, UserRegistrationSchema


@pytest.mark.asyncio
async def test_generate_staff_link(client_fixture):
    """Test generating link"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    admin = await initialize_admin(test_db)
    admin_user_data = UserRegistrationSchema(
        password=SUPER_ADMIN_PASSWORD,
        email=SUPER_ADMIN_EMAIL_ADDRESS,
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

    role = await validate_role_token(VerifyEmailAndSignUserUpSchema(
        code = "1234",
        role_token = token,
        email='bulaba@gmail.com',
        first_name = "Jacob",
        pin="whatchamcallit"
    ),test_db)
    assert role