import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_verify_backup_code(client_fixture):
    """Test verifying backup code"""
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
    assert setup_response.status_code == 201
    backup_codes = setup_response.json()['backup_codes']
    secret = setup_response.json()['secret']

    # Verify setup with TOTP
    verify_data = {"code": pyotp.TOTP(secret).now()}
    response_verify = await httpx_client.post(
        "/2fa/verify/",
        json=verify_data,
        headers=headers
    )
    assert response_verify.status_code == 200

    # Use backup code
    backup_verify_data = {"code": backup_codes[0]}
    response = await httpx_client.post(
        "/2fa/verify-backup/",
        json=backup_verify_data,
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['verified'] is True
    assert "consumed" in json_response['message']