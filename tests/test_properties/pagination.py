import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.activity.test_controller.test_objects import area_template

@pytest.mark.asyncio
async def test_list_properties_with_pagination(client_fixture):
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

    # Create multiple properties
    cover_image = {
        "secure_url": "http://example.com/cover.jpg",
        "public_id": "cover123"
    }
    other_images = [{
        "secure_url": "http://example.com/cover.jpg",
        "public_id": "cover124"
    }]
    payload_template = {
        "price": "300000.00",
        "description": "A property for testing",
        "availability": "available",
        "type": "apartment",
        "cover_image": cover_image,
        "other_images": other_images,
        "features": {"bedrooms": 2, "bathrooms": 1, "parking": True},
        "area": {**area_template},
    }
    num_properties = 7
    for i in range(num_properties):
        payload = {
            **payload_template, 
            "title": f"Property {i+1}",
            "cover_image":{**cover_image, "public_id":f"cover{i}"},
            "other_images":[{
                **cover_image,
                "public_id":f"cover{i}{j}"
            } for j in range(2)]
        }
        resp = await httpx_client.post(
            "/properties/",
            json=payload,
            headers=headers
        )
        assert resp.status_code == 201

    # Fetch first page (limit 5)
    response = await httpx_client.get(
        "/properties/?limit=5&offset=0",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    assert data[0]["title"].startswith("Property")

    # Fetch second page (limit 5, offset 5)
    response2 = await httpx_client.get(
        "/properties/?limit=5&offset=5",
        headers=headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert isinstance(data2, list)
    # Should return the remaining properties (2 in this case)
    assert len(data2) == num_properties - 5
    assert data2[0]["title"].startswith("Property")