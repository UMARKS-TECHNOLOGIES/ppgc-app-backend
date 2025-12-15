"""
Test suite for logout endpoint functionality.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.auth.services import (
    fetch_access_token,
    get_password_hash,
)
from ppgc_backend.app.controllers.auth.models import RefreshSession
from ppgc_backend.tests.auth.test_user_creation import create_test_user, user_data


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client_fixture):
    """Test that logout endpoint revokes the refresh token."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create test user
    user = await create_test_user(test_db)

    # Call logout endpoint
    response = await httpx_client.post(
        "/auth/signin/",
        json={
            "email": user.email,
            "pin": user_data.pin, 
        }
    )
    assert response.status_code == 200
    json_resp = response.json()
    refresh = json_resp.get('refresh')
    assert refresh
    refresh_id = refresh['id']
    assert refresh_id
    access_token = json_resp['access_token']
    assert access_token

    # Call logout endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await httpx_client.delete(
        f"/auth/logout/{refresh_id}/",
        headers=headers
    )
    assert response.status_code == 204
    # Verify token is marked as revoked in DB
    revoked_session = (await test_db.execute(
        select(RefreshSession).where(RefreshSession.id == refresh_id)
    )).scalars().first()
    assert not revoked_session
