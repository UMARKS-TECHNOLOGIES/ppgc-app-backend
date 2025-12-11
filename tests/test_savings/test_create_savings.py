import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_create_daily_saving(client_fixture):
    """Test creating a new daily saving"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create a test user
    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a daily saving
    saving_data = {
        "name": "Monthly Savings",
        "amount": 500.0
    }

    response = await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )

    assert response.status_code == 201
    json_response = response.json()
    assert json_response['name'] == "Monthly Savings"
    assert json_response['amount'] == 500.0
    assert json_response['user_id'] == user.id
    assert 'id' in json_response
    assert 'created_at' in json_response
