from httpx import AsyncClient
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema

async def get_test_tokens(user_data: UserRegistrationSchema, httpx_client: AsyncClient) -> dict:
    # create user and refresh token
    response = await httpx_client.post(
        "/auth/signin/",
        json={
            "email": user_data.email,
            **(
                {
                    "pin": user_data.pin, 
                } if user_data.pin else {
                    "password": user_data.password
                }
            )
        }
    )
    assert response.status_code == 200
    assert "session_id" in httpx_client.cookies
    json_resp = response.json()
    refresh = json_resp.get('refresh')
    assert refresh
    refresh_id = refresh['id']
    refresh_token = refresh['token']
    assert refresh_id
    assert refresh_token
    access_token = json_resp['access_token']
    assert access_token
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_id": refresh_id,
    }

async def signin_and_get_test_access_token(user_data, httpx_client):
    return (await get_test_tokens(user_data, httpx_client))['access_token']

async def signin_for_access_token(user_data, httpx_client):
    return (await get_test_tokens(user_data, httpx_client))['access_token']