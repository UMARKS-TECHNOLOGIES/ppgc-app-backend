import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template, room_data_template
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user, UserRegistrationSchema

@pytest.mark.asyncio
async def test_create_room(client_fixture):
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

    # Create hotel first
    hotel_data = {**hotel_data_template}
    response = await httpx_client.post(
        "/hotel/",
        json=hotel_data,
        headers=headers,
    )
    assert response.status_code == 201
    created_hotel = response.json()
    hotel_id = created_hotel["id"]

    # Prepare room data
    room_data = {**room_data_template}

    # create another staff 
    new_user = await create_test_user(test_db, user_data = UserRegistrationSchema(
        email="new_user@example.com",
        pin="password123",
        first_name="John",
        last_name="Doe",
        user_role="staff"
    ))
    new_token = fetch_access_token(user=new_user)["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}
    response = await httpx_client.post(
        f"/hotel/{hotel_id}/create-room/",
        json=room_data,
        headers=new_headers,
    )
    assert response.status_code == 403

    # Create room
    response = await httpx_client.post(
        f"/hotel/{hotel_id}/create-room/",
        json=room_data,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["room_type"] == room_data["room_type"]
    assert data["price_per_night"] == room_data["price_per_night"]
    assert data["status"] == "available"
