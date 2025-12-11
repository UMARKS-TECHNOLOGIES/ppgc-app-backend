import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_get_savings_this_month(client_fixture):
    """Test retrieving savings for this month"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create multiple savings
    savings_list = [
        {"name": "Saving 1", "amount": 100.0},
        {"name": "Saving 2", "amount": 200.0},
        {"name": "Saving 3", "amount": 150.0},
    ]

    for saving_data in savings_list:
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve savings for this month
    response = await httpx_client.get(
        "/savings/period?period=this_month",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_month"
    assert json_response['total_amount'] == 450.0
    assert json_response['transaction_count'] == 3
    assert len(json_response['transactions']) == 3
