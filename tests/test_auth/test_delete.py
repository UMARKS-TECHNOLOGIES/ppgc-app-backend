import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth import signin_for_access_token
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user, UserRegistrationSchema, user_data


@pytest.mark.asyncio
async def test_act_deletion(client_fixture):
    httpx_client: AsyncClient = client_fixture['http_client']
    test_db: AsyncSession = client_fixture['db']

    # Create user and get token
    _ = await create_test_user(test_db)
    response = await httpx_client.post(
        "/auth/signin/",
        json={
            "email": user_data.email,
            "pin": user_data.pin, 
        }
    )
    assert response.status_code == 200
    json_resp = response.json()
    access_token = json_resp['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    
    #------------------------------
    # Make deletion request
    #------------------------------
    response = await httpx_client.delete(
        "/auth/delete-account/", 
        headers=headers
    )
    assert response.status_code == 204

    #------------------------------
    # Make signin request
    #------------------------------
    response = await httpx_client.post(
        "/auth/signin/", 
        json={
            "email": user_data.email,
            "pin": user_data.pin
        },
        headers=headers
    )
    assert response.status_code == 400