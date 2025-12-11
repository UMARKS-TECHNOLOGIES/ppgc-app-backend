import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_get_savings_this_week(client_fixture):
    """Test retrieving savings for this week"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a saving for this week
    saving_data = {
        "name": "This Week Saving",
        "amount": 250.0
    }

    create_response = await httpx_client.post(
        "/savings/create",
        json=saving_data,
        headers=headers
    )
    assert create_response.status_code == 201

    # Retrieve savings for this week
    response = await httpx_client.get(
        "/savings/period?period=this_week",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_week"
    assert json_response['total_amount'] == 250.0
    assert json_response['transaction_count'] == 1
    assert len(json_response['transactions']) == 1
    assert json_response['transactions'][0]['amount'] == 250.0