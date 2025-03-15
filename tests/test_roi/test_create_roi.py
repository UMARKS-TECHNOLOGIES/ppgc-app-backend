import pytest

from ppgc_backend.app.controllers.auth import (
    fetched_access_token,
    create_user,
)
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
    roi_data = {
        "investment_amount": 10000,
        "interest_rate": 5.0
    }


    #**# create an investment
    # make assertions
    response = await client.post("/roi/create-investment", json=roi_data, headers=headers)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response.get("investment_amount") == roi_data["investment_amount"]
    assert json_response.get("interest_rate") == roi_data["interest_rate"]
    assert json_response.get("status") == 'active'
    # get the id of the investment instance
    investment_instance_id = json_response.get("id")

    #**# create an investment
    # make assertions
    response = await client.get(f"/roi/get-investment/{investment_instance_id}", headers=headers)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response.get("investment_amount") == roi_data["investment_amount"]
    assert json_response.get("interest_rate") == roi_data["interest_rate"]
    # assert json_response.get("roi") == expected_return
    assert json_response.get("status") == 'active'