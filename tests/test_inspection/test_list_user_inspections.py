import pytest
from httpx import AsyncClient
from datetime import date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth.test_user_creation import create_test_user
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema
from ppgc_backend.tests.property.test_property_creation import create_test_property
from ppgc_backend.app.models import Inspection, User

@pytest.mark.asyncio
async def test_list_user_inspections(client_fixture):
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

    # Create inspections for this user
    inspections = [
        Inspection(
            property_id=property.id,
            call_number="+234 9033193240",
            date_of_inspection=date.today() + timedelta(days=i),
            time_of_inspection=time.max,
            requester_id=created_user.id
        ) for i in range(3)
    ]
    test_db.add_all(inspections)
    await test_db.commit()

    # Create inspections for another user (should not be returned)
    other_user: User = await create_test_user(
        test_db,
        user_data = UserRegistrationSchema(
        email="satoshi@example.com",
        pin="password123",
        first_name="Satoshi",
        last_name="Nakamoto",
    ))
    other_inspections = [
        Inspection(
            property_id=property.id,
            call_number="+234 9033193241",
            date_of_inspection=date.today() + timedelta(days=i),
            time_of_inspection=time.max,
            requester_id=other_user.id
        ) for i in range(2)
    ]
    test_db.add_all(other_inspections)
    await test_db.commit()

    # Make request to /inspections/my-inspections
    response = await httpx_client.get(
        "/inspections/my-inspections",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(inspections)
    for item in data:
        assert item["requester_id"] == created_user.id
