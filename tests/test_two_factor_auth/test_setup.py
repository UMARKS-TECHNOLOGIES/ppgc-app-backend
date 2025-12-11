import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token


@pytest.mark.asyncio
async def test_setup_2fa_totp(client_fixture):
    """Test setting up TOTP 2FA"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup 2FA
    setup_data = {
        "method": "totp"
    }

    response = await httpx_client.post(
        "/2fa/setup",
        json=setup_data,
        headers=headers
    )

    assert response.status_code == 201
    json_response = response.json()
    assert 'secret' in json_response
    assert 'qr_code_url' in json_response
    assert 'backup_codes' in json_response
    assert json_response['method'] == "totp"
    assert len(json_response['backup_codes']) == 10
    assert json_response['secret'].isalnum()
