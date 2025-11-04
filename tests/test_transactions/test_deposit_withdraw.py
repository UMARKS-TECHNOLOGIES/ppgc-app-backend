import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import trx_data
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_deposit_withdraw(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create and authenticate user
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create a deposit transaction
    response = await httpx_client.post(
        '/trx/deposit/',
        json=trx_data,
        headers=headers
    )
    assert response.status_code == 200
    trx_resp = response.json()
    assert "id" in trx_resp
    assert trx_resp['trx_type'] == 'deposit'

    # create a withdrawal transaction with same trx_id and assert an error
    response = await httpx_client.post(
        '/trx/withdraw/',
        json=trx_data,
        headers=headers
    )
    assert response.status_code == 409
    
    # Make a good trx request
    trx_data['trx_id'] = "e8a7b6"
    response = await httpx_client.post(
        '/trx/withdraw/',
        json=trx_data,
        headers=headers
    )
    assert response.status_code == 200
    trx_resp = response.json()
    assert "id" in trx_resp
    assert trx_resp['trx_type'] == 'withdraw'