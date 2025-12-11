import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_get_2fa_status(client_fixture):
    """Test retrieving 2FA status"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {"method": "totp"}
    setup_response = await httpx_client.post(
        "/2fa/setup/",
        json=setup_data,
        headers=headers
    )
    secret = setup_response.json()['secret']

    # Verify setup
    verify_data = {"code": pyotp.TOTP(secret).now()}
    await httpx_client.post(
        "/2fa/verify/",
        json=verify_data,
        headers=headers
    )

    # Get status
    response = await httpx_client.get(
        "/2fa/status/",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['user_id'] == user.id
    assert json_response['is_enabled'] is True
    assert json_response['verified'] is True
    assert json_response['method'] == "totp"

