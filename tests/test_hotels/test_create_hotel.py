import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token, initialize_admin

@pytest.mark.asyncio
async def test_create_hotel(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break
    
    # Create and authenticate user
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Prepare hotel data
    hotel_data = {
        **hotel_data_template
    }

    # Create hotel
    response = await httpx_client.post(
        "/hotel/",
        json=hotel_data,
        headers=headers,
    )
    assert response.status_code == 403

    # Elevate user's role
    admin = await initialize_admin()
    token = fetch_access_token(user=admin)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = await httpx_client.post(
        "/hotel/",
        json=hotel_data,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == hotel_data["name"]
    assert data["cover_image"]['secure_url'] == hotel_data["cover_image"]['secure_url']
    assert data['total_rooms'] == 0
