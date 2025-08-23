import pytest

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from ppgc_backend.app.models import (
    Area,
    Property, 
)
from ppgc_backend.tests.activity.test_controller.test_objects import area_template

# test utility functions
async def create_test_property(test_db: AsyncSession):
    """
    Helper function to create a test asset for other tests.
    """
    property = Property(
        title="Test Asset",
        currency="USD",
        status="auction",
        price=100000.00,
        description="Test description",
        availability="available",
        area = Area(
            **area_template,
        ),
        category="House",
        features={},
    )
    test_db.add(property)
    await test_db.commit()
    return property


@pytest.mark.asyncio
async def test_create_property(client_fixture):
    async for fixture_obj in client_fixture:
        test_db: AsyncSession = fixture_obj["db"]
        break

    property = await create_test_property(test_db)
    stmt = await test_db.execute(
        select(Property)
        .where(Property.id == property.id)
    )
    result = stmt.scalars().first()
    assert result