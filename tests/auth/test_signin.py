import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import User
from .test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema


@pytest.mark.asyncio
async def test_route_signin(client_fixture):
    # Extract the fixture object
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj['db']
        httpx_client: AsyncClient = fixture_obj['http_client']
        break
    
    user_data = UserRegistrationSchema(
        email="test@example.com",
        pin="password123",
        first_name="John",
        last_name="Doe",
    )

    # Call the create_user function
    created_user = await create_test_user(test_db, user_data)

    json_data = {
        'email': created_user.email,
        'pin': user_data.pin
    }
    response = await httpx_client.post(
        "/auth/signin",
        json=json_data  # Use json instead of data for a JSON body
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['token_type'] == "bearer"
    assert "access_token" in json_response