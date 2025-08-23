import pytest
from httpx import AsyncClient
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.property.test_property_creation import create_test_property
from ppgc_backend.app.models import Inspection, User

@pytest.mark.asyncio
async def test_update_inspection(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Create and authenticate user
    created_user: User = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    # Create test property
    property = await create_test_property(test_db)

    # Create an inspection (status should be 'pending' by default)
    inspection = Inspection(
        property_id=property.id,
        call_number="+234 9033193240",
        date_of_inspection=date.today(),
        time_of_inspection=time.max,
        requester_id=created_user.id,
        status="pending"
    )
    test_db.add(inspection)
    await test_db.commit()
    await test_db.refresh(inspection)

    #**# Update the inspection (should succeed)
    update_payload = {
        "call_number": "+234 1111111111",
    }
    response = await httpx_client.patch(
        f"/inspections/{inspection.id}",
        json=update_payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == inspection.id
    assert data["call_number"] == update_payload["call_number"]

    #**# Change status to something other than 'pending'
    inspection.status = "confirmed"
    test_db.add(inspection)
    await test_db.commit()
    await test_db.refresh(inspection)

    # Try to update again (should fail)
    response = await httpx_client.patch(
        f"/inspections/{inspection.id}",
        json={"call_number": "+234 2222222222"},
        headers=headers,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Only inspections with status 'pending' can be modified"
