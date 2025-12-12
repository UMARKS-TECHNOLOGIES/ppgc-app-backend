import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import User
from .test_user_creation import create_test_user, user_data
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema


@pytest.mark.asyncio
async def test_route_signin(client_fixture):
    # Extract the fixture object
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj['db']
        httpx_client: AsyncClient = fixture_obj['http_client']
        break

    # Call the create_user function
    created_user = await create_test_user(test_db, user_data)

    json_data = {
        'email': created_user.email,
        'pin': user_data.pin
    }
    response = await httpx_client.post(
        "/auth/signin/",
        json=json_data  # Use json instead of data for a JSON body
    )
    assert response.status_code == 200
    json_response: dict = response.json()
    assert json_response.get("access_token")
    assert "id" in json_response
    assert json_response['email'] == user_data.email
    assert json_response['user_role'] == 'user'
    assert not json_response['email_verified']
    refresh = json_response.get('refresh')
    refresh_id = refresh.get('id')
    assert refresh_id
    refresh_token = refresh['token']
    assert refresh_token

    #====================
    # Test refresh
    #====================
    response = await httpx_client.post(
        f'/auth/refresh/{refresh_id}/',
        json=refresh_token,
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert "access_token" in json_resp