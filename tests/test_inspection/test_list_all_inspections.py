import pytest
from httpx import AsyncClient
from datetime import date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.property.test_property_creation import create_test_property
from ppgc_backend.app.models import Inspection, User


@pytest.mark.asyncio
async def test_list_all_inspections(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        httpx_client: AsyncClient = fixture_obj["http_client"]
        break

    # Generate an access token for authentication
    created_user: User = await create_test_user(test_db)
    token = fetch_access_token(user=created_user)['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    # Make an unauthorized request
    response = await httpx_client.get(
        "/inspections/all", 
        headers=headers,
    )
    assert response.status_code == 403

    # elevate the role of the user
    created_user.user_role = 'staff'
    test_db.add(created_user)
    
    # create test property
    property = await create_test_property(test_db)
    # create multiple Inpection
    inspections = [
        Inspection(
            property_id=property.id,
            call_number="+234 9033193240",
            date_of_inspection= date.today()+timedelta(hours=i),
            time_of_inspection= time.max, 
            requester_id=created_user.id
        ) for i in range(5)
    ]
    test_db.add_all(inspections)

    # commit all changes
    await test_db.commit()
    

    # Make an authorized request
    response = await httpx_client.get(
        "/inspections/all", 
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(inspections)