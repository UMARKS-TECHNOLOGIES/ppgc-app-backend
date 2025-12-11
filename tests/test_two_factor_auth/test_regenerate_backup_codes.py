import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user, user_data
from ppgc_backend.app.controllers.auth.services import fetch_access_token


@pytest.mark.asyncio
async def test_regenerate_backup_codes(client_fixture):
    """Test regenerating backup codes"""
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
    old_backup_codes = setup_response.json()['backup_codes']
    secret = setup_response.json()['secret']

    # Verify setup
    verify_data = {"code": pyotp.TOTP(secret).now()}
    await httpx_client.post(
        "/2fa/verify/",
        json=verify_data,
        headers=headers
    )

    # Regenerate codes
    regen_data = {"pin": user_data.pin}
    response = await httpx_client.post(
        "/2fa/regenerate-backup-codes/",
        json=regen_data,
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    new_backup_codes = json_response['backup_codes']
    assert len(new_backup_codes) == 10
    assert new_backup_codes != old_backup_codes
