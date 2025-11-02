import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token



@pytest.mark.asyncio
async def test_confirm_passcode(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break
    
    # Create and authenticate user
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pass_code = '1234'
    response = await httpx_client.post(
        '/settings/update-passcode/',
        json={'pass_code': pass_code},
        headers=headers
    )
    assert response.status_code == 200

    response = await httpx_client.post(
        '/auth/confirm-passcode/',
        json={'pass_code': pass_code},
        headers=headers
    )
    assert response.status_code == 200
