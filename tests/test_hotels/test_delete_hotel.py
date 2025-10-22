import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_delete_hotel(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create and authenticate user
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Elevate user's role
    created_user.user_role = 'staff'
    test_db.add(created_user)
    await test_db.commit()

    # Create hotel
    hotel_data = {**hotel_data_template}
    response = await httpx_client.post(
        "/hotel/",
        json=hotel_data,
        headers=headers,
    )
    assert response.status_code == 201
    created_hotel = response.json()
    hotel_id = created_hotel["id"]
    assert created_hotel['manager_id'] == created_user.id

    # Delete hotel
    response = await httpx_client.delete(
        f"/hotel/{hotel_id}/",
        headers=headers,
    )
    assert response.status_code == 204

    # Try to get the deleted hotel (should return 404)
    response = await httpx_client.get(
        f"/hotel/{hotel_id}/",
        headers=headers,
    )
    assert response.status_code == 404
