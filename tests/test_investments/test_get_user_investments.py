import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


from ppgc_backend.app.controllers.auth.services import (
    fetch_access_token,
)
from ppgc_backend.tests.test_transactions import trx_data
from ppgc_backend.app.controllers.investments.models import Investment
from ppgc_backend.app.controllers.investments.tools import compute_roi
from ppgc_backend.tests.auth.test_user_creation import create_test_user

@pytest.mark.asyncio
async def test_get_user_investments(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj.get("db")
        httpx_client: AsyncClient = fixture_obj.get("http_client")
        break

    created_user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=created_user)
    token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    roi_data = {
        "name": "Investment",
        "amount": 10000.0,
        "interest_rate": 5.0,
        "duration": 8,
        "trx": trx_data,
    }

    n = 5
    #**# create investments
    for i in range(n):
        response = await httpx_client.post(
            "/investments/create/", 
            json={
                **roi_data,
                "trx": {
                    **roi_data["trx"],
                    "trx_id": f"xoxo{i}",
                }
            }, 
            headers=headers
        )
        assert response.status_code == 200
        json_response = response.json()
        assert 'id' in json_response


    #**# get all investments
    response = await httpx_client.get(
        f"/investments/", 
        headers=headers
    )
    assert response.status_code == 200
    json_response = response.json()
    # make assertions
    assert len(json_response) == n