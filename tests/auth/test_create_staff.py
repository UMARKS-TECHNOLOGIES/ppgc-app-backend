import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


from ppgc_backend.app.models import User, TransientVerificationStore
from ppgc_backend.app.controllers.auth.schemas import UserRegistrationSchema
from ppgc_backend.app.controllers.auth.services import (
    create_user, 
    verify_password,
)


user_data = UserRegistrationSchema(
    email="test@example.com",
    password="password123",
    first_name="John",
    last_name="Doe",
)
async def create_test_user(
    db: AsyncSession,
    user_data = user_data,
):
    return await create_user(db, user_data)


@pytest.mark.asyncio
async def test_create_staff(client_fixture):
    # Unpack the fixture
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    email = user_data.email
    password = user_data.password

    payload = {
        "email": email,
        "password": password,
    }

    # Request verification code
    response = await httpx_client.post(
        "/auth/register-staff",
        json=payload
    )
    assert response.status_code == 201
    json_response = response.json()
    assert 'id' in json_response
    assert not json_response['email_verified']

    # Check that it's stored in the DB
    query = await test_db.execute(
        select(User)
        .where(
            User.email == email
        )
    )
    user = query.scalars().first()
    assert user is not None
    assert not user.email_verified
