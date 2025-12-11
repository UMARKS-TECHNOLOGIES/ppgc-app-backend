import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token


@pytest.mark.asyncio
async def test_get_savings_this_year(client_fixture):
    """Test retrieving savings for this year"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create savings
    for i in range(5):
        saving_data = {
            "name": f"Saving {i+1}",
            "amount": float((i+1) * 100)
        }
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve savings for this year
    response = await httpx_client.get(
        "/savings/period?period=this_year",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['period'] == "this_year"
    assert json_response['transaction_count'] == 5
    assert json_response['total_amount'] == 1500.0  # 100 + 200 + 300 + 400 + 500