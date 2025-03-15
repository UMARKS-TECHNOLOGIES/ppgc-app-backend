import pytest

from ppgc_backend.app.controllers.auth import (
    fetched_access_token,
    create_user,
)
from ppgc_backend.app.models import Investment
from ppgc_backend.app.schemas.auth_schemas import UserRegistrationSchema

@pytest.mark.asyncio
async def test_create_roi(client__fixture):
    async for fixture_obj in client__fixture:
        test_db = fixture_obj.get("db")
        client = fixture_obj.get("http_client")
        break

    user_data = UserRegistrationSchema(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    created_user = await create_user(test_db, user_data)
    token_obj = fetched_access_token(user=created_user)
    token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {token}"}


    #expected_return= 15000
    investments = [
        Investment(
            investment_amount= 10000+i,
            interest_rate= 5.0+i,
            user_id = created_user.id
        ) 
        for i in range(10)
    ]
    test_db.add_all(investments)
    await test_db.commit()


    #**# create an investment
    # make assertions
    response = await client.get("/roi/get-investments", headers=headers)
    assert response.status_code == 200
    json_response = response.json()
    # Validate the structure of each asset
    required_keys = {
        "id",
        "status",
        "investment_amount",
        "interest_rate",
        "created_at",
        "updated_at",
        "roi",
    }
    for investment in json_response:
        assert all(key in investment for key in required_keys)