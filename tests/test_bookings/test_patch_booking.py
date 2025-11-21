import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import booking_data_template
from ..test_hotels import hotel_data_template, room_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

@pytest.mark.asyncio
async def test_patch_booking(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create and authenticate user
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Elevate user's role for hotel/room creation
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
        f"/hotel/{hotel_id}/create-room/",
        json=room_data,
        headers=headers,
    )
    assert response.status_code == 201
    created_room = response.json()
    room_id = created_room["id"]

    # Create booking (include hotel_id)
    booking_data = {
        "room_id": room_id,
        "hotel_id": hotel_id,
        **booking_data_template,
    }
    response = await httpx_client.post(
        "/bookings/",
        json=booking_data,
        headers=headers,
    )
    assert response.status_code == 201
    created_booking = response.json()
    booking_id = created_booking["id"]

    # Patch booking (e.g., change guests)
    patch_data = {"guests": 3}
    response = await httpx_client.patch(
        f"/bookings/{booking_id}/",
        json=patch_data,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == booking_id
    assert data["guests"] == 3
