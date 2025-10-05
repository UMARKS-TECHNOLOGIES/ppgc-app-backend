import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import payload
from ppgc_backend.app.controllers.properties.models import Property
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.activity.test_controller.test_objects import area_template

@pytest.mark.asyncio
async def test_update_property(client_fixture):
    # Extract fixture objects
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

    # --- Step 1: Create a property to update
    create_response = await httpx_client.post(
        "/properties/",
        json=payload,
        headers=headers
    )
    assert create_response.status_code == 201
    property_id = create_response.json()["id"]

    # --- Step 2: Prepare update payload & Send update request
    update_payload = {
        "title": "Updated Luxury Apartment",
        "price": "600000.00",
        "description": "An updated beautiful 3-bedroom apartment in Lekki",
        "availability": "unavailable",
        "features": ["parking"],
    }
    update_response = await httpx_client.patch(
        f"/properties/{property_id}/",
        json=update_payload,
        headers=headers
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == update_payload["title"]
    assert str(data["price"]) == update_payload["price"]
    assert data["availability"] == update_payload["availability"]
    assert "parking" in data["features"]
    # --- Step 2b: Check DB persistence
    updated_property = await test_db.get(Property, property_id)
    assert updated_property is not None
    assert updated_property.title == update_payload["title"]
    assert str(updated_property.price) == update_payload["price"]
    assert updated_property.availability == update_payload["availability"]