import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import Area
from ppgc_backend.app.models import CloudImageDetail
from ppgc_backend.app.controllers.properties.models import Property
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.app.controllers.properties.schemas import PropertyCreate
from ppgc_backend.tests.activity.test_controller.test_objects import area_template

@pytest.mark.asyncio
async def test_add_property(client_fixture):
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
    
    # --- Step 1: Create dependencies (Area + CloudImageDetail)
    cover_image = {
        "secure_url":"http://example.com/cover.jpg",
        "public_id":"cover123"
    }
    other_images = [{
        "secure_url":"http://example.com/cover.jpg",
        "public_id":"cover124"
    }]

    # --- Step 2: Prepare payload
    payload = {
        "title": "Luxury Apartment",
        "price": "500000.00",   # Decimal must be str in JSON
        "description": "A beautiful 3-bedroom apartment in Lekki",
        "availability": "available",
        "type": "apartment",
        "cover_image": cover_image,
        "other_images": other_images,
        "features": {"bedrooms": 3, "bathrooms": 2, "parking": True},
        "area": {**area_template},
    }

    # --- Step 3: Send request
    response = await httpx_client.post(
        "/properties/", 
        json=payload,
        headers=headers
    )

    # --- Step 4: Validate response
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert str(data["price"]) == payload["price"]
    assert data["availability"] == "available"

    # --- Step 5: Check DB persistence
    created_property = await test_db.get(Property, data["id"])
    assert created_property is not None
    assert created_property.title == payload["title"]
