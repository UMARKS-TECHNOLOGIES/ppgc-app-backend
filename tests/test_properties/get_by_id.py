import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.activity.test_controller.test_objects import area_template

@pytest.mark.asyncio
async def test_get_property(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create and authenticate user
    created_user = await create_test_user(test_db)
    created_user.user_role = 'staff'
    test_db.add(created_user)
    await test_db.commit()
    token = fetch_access_token(user=created_user)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a property
    cover_image = {
        "secure_url": "http://example.com/cover.jpg",
        "public_id": "cover123"
    }
    other_images = [{
        "secure_url": "http://example.com/cover.jpg",
        "public_id": "cover124"
    }]
    payload = {
        "title": "Test Property",
        "price": "300000.00",
        "description": "A property for testing",
        "availability": "available",
        "type": "apartment",
        "cover_image": cover_image,
        "other_images": other_images,
        "features": {"bedrooms": 2, "bathrooms": 1, "parking": True},
        "area": {**area_template},
    }
    create_response = await httpx_client.post(
        "/properties/",
        json=payload,
        headers=headers
    )
    assert create_response.status_code == 201
    property_id = create_response.json()["id"]

    # Retrieve the property
    get_response = await httpx_client.get(
        f"/properties/{property_id}/",
        headers=headers
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == property_id
    assert data["title"] == payload["title"]