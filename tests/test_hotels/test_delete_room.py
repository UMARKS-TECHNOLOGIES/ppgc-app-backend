import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template, room_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_delete_room_by_id(client_fixture):
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

    # Create room
    room_data = {**room_data_template, "hotel_id": hotel_id}
    response = await httpx_client.post(
        "/hotel/create-room/",
        json=room_data,
        headers=headers,
    )
    assert response.status_code == 201
    created_room = response.json()
    room_id = created_room["id"]

    # Delete room by id
    response = await httpx_client.delete(
        f"/hotel/rooms/{room_id}",
        headers=headers,
    )
    assert response.status_code == 204

    # Try to get the deleted room (should return 404)
    response = await httpx_client.get(
        f"/hotel/rooms/{room_id}",
        headers=headers,
    )
    assert response.status_code == 404
