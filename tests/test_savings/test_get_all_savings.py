import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token


@pytest.mark.asyncio
async def test_get_all_savings_with_pagination(client_fixture):
    """Test retrieving all savings with pagination"""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create 10 savings
    for i in range(10):
        saving_data = {
            "name": f"Saving {i+1}",
            "amount": float((i+1) * 50)
        }
        await httpx_client.post(
            "/savings/create",
            json=saving_data,
            headers=headers
        )

    # Retrieve all savings with limit
    response = await httpx_client.get(
        "/savings/all?limit=5&offset=0",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 5
    assert json_response[0]['amount'] == 500.0  # Most recent (10 * 50)

    # Retrieve next page
    response = await httpx_client.get(
        "/savings/all?limit=5&offset=5",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 5
    assert json_response[0]['amount'] == 250.0  # (5 * 50)
