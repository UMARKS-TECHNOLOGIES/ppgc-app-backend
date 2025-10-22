import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template, room_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token

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

    n = 5
    for i in range(n):
        # Prepare room data
        room_data = {
            **room_data_template,
            "cover_image": {"secure_url": "https://example.com/img1.jpg", "public_id": f"cover{i}"},
            "other_images": [
                {"secure_url": "https://example.com/img2.jpg", "public_id": f"other{i}"}
            ],
        }
        # Create room
        response = await httpx_client.post(
            f"/hotel/{hotel_id}/create-room/",
            json=room_data,
            headers=headers,
        )
        assert response.status_code == 201

    # Create room
    response = await httpx_client.get(
        f"/hotel/{hotel_id}/rooms/",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == n