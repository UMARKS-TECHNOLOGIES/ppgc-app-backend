import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template, room_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.app.controllers.hotels.enums import RoomStatus


@pytest.mark.asyncio
async def test_get_all_available_rooms(client_fixture):
    """Test retrieving all available rooms from all hotels with pagination."""
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create and authenticate user
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Elevate user's role to staff
    created_user.user_role = 'staff'
    test_db.add(created_user)
    await test_db.commit()

    # Create two hotels
    hotel_ids = []
    for h in range(2):
        hotel_data = {**hotel_data_template}
        response = await httpx_client.post(
            "/hotel/",
            json=hotel_data,
            headers=headers,
        )
        assert response.status_code == 201
        created_hotel = response.json()
        hotel_ids.append(created_hotel["id"])

    # Create rooms in each hotel (some available, some not)
    available_count = 0
    for hotel_id in hotel_ids:
        for i in range(3):
            room_data = {
                **room_data_template,
                "cover_image": {"secure_url": "https://example.com/img1.jpg", "public_id": f"cover_{hotel_id}_{i}"},
            }
            response = await httpx_client.post(
                f"/hotel/{hotel_id}/create-room/",
                json=room_data,
                headers=headers,
            )
            assert response.status_code == 201
            available_count += 1

    # Fetch all available rooms
    response = await httpx_client.get(
        "/hotel/rooms/available/all/?page=1&size=20",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify we got the available rooms
    assert len(data) == available_count
    assert all(room["status"] == RoomStatus.available.value for room in data)


@pytest.mark.asyncio
async def test_get_all_available_rooms_pagination(client_fixture):
    """Test pagination for available rooms endpoint."""
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
    hotel_id = response.json()["id"]

    # Create 25 rooms
    for i in range(25):
        room_data = {
            **room_data_template,
            "room_number": f"R{i:03d}",
            "cover_image": {"secure_url": "https://example.com/img1.jpg", "public_id": f"cover_{i}"},
        }
        response = await httpx_client.post(
            f"/hotel/{hotel_id}/create-room/",
            json=room_data,
            headers=headers,
        )
        assert response.status_code == 201

    # Fetch page 1 with size 20
    response = await httpx_client.get(
        "/hotel/rooms/available/all/?page=1&size=20",
        headers=headers,
    )
    assert response.status_code == 200
    page1_data = response.json()
    assert len(page1_data) == 20

    # Fetch page 2 with size 20
    response = await httpx_client.get(
        "/hotel/rooms/available/all/?page=2&size=20",
        headers=headers,
    )
    assert response.status_code == 200
    page2_data = response.json()
    assert len(page2_data) == 5

    # Verify no room IDs overlap between pages
    page1_ids = {room["id"] for room in page1_data}
    page2_ids = {room["id"] for room in page2_data}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_get_all_available_rooms_empty(client_fixture):
    """Test retrieving available rooms when none exist."""
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Fetch available rooms (should be empty by default)
    response = await httpx_client.get(
        "/hotel/rooms/available/all/?page=1&size=20",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
