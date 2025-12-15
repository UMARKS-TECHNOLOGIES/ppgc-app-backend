"""
Test suite for user settings endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.tests.auth import signin_for_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user, user_data


@pytest.mark.asyncio
async def test_get_user_settings(client_fixture):
    """Test retrieving user settings."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    access_token = await signin_for_access_token(user_data, httpx_client)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await httpx_client.get(
        "/settings/",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response['first_name'] == user.first_name
    assert json_response['last_name'] == user.last_name
    assert json_response['email_notification'] == user.email_notification
    assert json_response['push_notification'] == user.push_notification
