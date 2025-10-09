import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from . import hotel_data_template
from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token, initialize_admin

@pytest.mark.asyncio
async def test_get_all_hotels(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break
    
    # Create and authenticate admin user
    admin = await initialize_admin()
    token = fetch_access_token(user=admin)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a hotel to ensure there is at least one
    n = 9
    for i in range(n):
        hotel_data = { 
            **hotel_data_template,
            'cover_image': {
                **hotel_data_template['cover_image'],
                'public_id': f'img{i}'
            },
            'other_images':[
                {             
                    **hotel_data_template['cover_image'],
                    'public_id': f'img{i}{j}'
                } for j in range (2)
            ],
        }
        response = await httpx_client.post(
            "/hotel/",
            json=hotel_data,
            headers=headers,
        )
        assert response.status_code == 201

    # Get first pagination
    size=5
    response = await httpx_client.get(
        f"/hotel/all/?page=1&size={size}",
    )
    assert response.status_code == 200
    hotels = response.json()
    assert isinstance(hotels, list)
    assert len(hotels) == size

    # Get second pagination
    response = await httpx_client.get(
        f"/hotel/all/?page=2&size={size}",
    )
    assert response.status_code == 200
    hotels = response.json()
    assert isinstance(hotels, list)
    assert len(hotels) == (n-size)
