import pytest
from httpx import AsyncClient
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.property.test_property_creation import create_test_property


@pytest.mark.asyncio
async def test_create_inspection(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    property = await create_test_property(test_db)
    payload = {
        "property_id": property.id,
        "call_number": "+234 9033193240",
        "date_of_inspection": date.today().isoformat(),
        "time_of_inspection": time.max.isoformat(), 
    }
    
    # Generate an access token for authentication
    created_user = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)['access_token']
    headers = {"Authorization": f"Bearer {token}"}


    response = await httpx_client.post(
        "/inspections/", 
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == property.id