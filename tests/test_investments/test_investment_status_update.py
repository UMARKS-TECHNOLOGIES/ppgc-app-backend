import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.controllers.auth.services import (
    fetch_access_token,
)
from ppgc_backend.tests.test_transactions import trx_data
from ppgc_backend.tests.auth.test_user_creation import create_test_user


@pytest.mark.asyncio
async def test_investment_status_update(client_fixture):
    """Test the withdrawal endpoint, ensuring ROI is computed properly."""
    
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj.get("db")
        httpx_client: AsyncClient = fixture_obj.get("http_client")
        break

    created_user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=created_user)
    token = token_obj["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    roi_data = {
        "name": "Investment",
        "amount": 10000.0,
        "interest_rate": 5.0,
        "duration": 8,
        "trx": trx_data,
    }


    #**# create an investment
    response = await httpx_client.post(
        "/investments/create/", 
        json=roi_data, 
        headers=headers
    )
    assert response.status_code == 200
    json_response = response.json()
    
    # ----------------------------
    # update investment
    # ----------------------------
    assert 'id' in json_response
    status = 'completed'
    id = json_response['id']
    response = await httpx_client.patch(
        f"/investments/{id}/", 
        json={"status": status}, 
        headers=headers
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['status'] == status


    # ----------------------------
    # Try re-updating investment
    # ----------------------------
    response = await httpx_client.patch(
        f"/investments/{id}/", 
        json={"status": status}, 
        headers=headers
    )
    assert response.status_code == 403
