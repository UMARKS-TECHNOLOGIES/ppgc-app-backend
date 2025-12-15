"""
Test suite for logout endpoint functionality.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.token_management.models import RefreshSession
from ppgc_backend.app.controllers.auth.services import (
    fetch_access_token,
    get_password_hash,
)
from ppgc_backend.tests.auth.test_user_creation import create_test_user


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client_fixture):
    """Test that logout endpoint revokes the refresh token."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create test user
    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a refresh token for the user
    refresh_token = RefreshSession(
        user_id=user.id,
        token="test_refresh_token_123",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False
    )
    test_db.add(refresh_token)
    await test_db.commit()
    await test_db.refresh(refresh_token)

    # Call logout endpoint
    response = await httpx_client.post(
        f"/auth/logout/{refresh_token.id}/",
        headers=headers
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "detail" in json_response
    assert "revoked" in json_response['detail'].lower()

    # Verify token is marked as revoked in DB
    stmt = await test_db.execute(
        select(RefreshSession).where(RefreshSession.id == refresh_token.id)
    )
    revoked_token = stmt.scalars().first()
    assert revoked_token is not None
    assert revoked_token.is_revoked is True


@pytest.mark.asyncio
async def test_logout_with_invalid_token_id(client_fixture):
    """Test logout with non-existent refresh token ID."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Try to logout with non-existent token ID
    response = await httpx_client.post(
        f"/auth/logout/99999/",
        headers=headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_logout_twice_with_same_token(client_fixture):
    """Test that logging out twice with same token returns already revoked message."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    user = await create_test_user(test_db)
    token_obj = fetch_access_token(user=user)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create refresh token
    refresh_token = RefreshSession(
        user_id=user.id,
        token="test_refresh_token_456",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False
    )
    test_db.add(refresh_token)
    await test_db.commit()
    await test_db.refresh(refresh_token)

    # First logout
    response1 = await httpx_client.post(
        f"/auth/logout/{refresh_token.id}/",
        headers=headers
    )
    assert response1.status_code == 200

    # Second logout attempt
    response2 = await httpx_client.post(
        f"/auth/logout/{refresh_token.id}/",
        headers=headers
    )
    assert response2.status_code == 200
    json_response = response2.json()
    assert "already revoked" in json_response['detail'].lower()


@pytest.mark.asyncio
async def test_logout_requires_authentication(client_fixture):
    """Test that logout endpoint requires valid authentication."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        break

    # Try to logout without token
    response = await httpx_client.post("/auth/logout/1/")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_logout_with_other_users_token(client_fixture):
    """Test that user cannot logout another user's refresh token."""
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # Create two users
    user1 = await create_test_user(test_db)
    user2 = await create_test_user(test_db)

    # Create refresh token for user2
    refresh_token = RefreshSession(
        user_id=user2.id,
        token="user2_refresh_token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False
    )
    test_db.add(refresh_token)
    await test_db.commit()
    await test_db.refresh(refresh_token)

    # Try to logout as user1 using user2's token ID
    token_obj = fetch_access_token(user=user1)
    access_token = token_obj['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await httpx_client.post(
        f"/auth/logout/{refresh_token.id}/",
        headers=headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()

    # Verify token is still not revoked
    stmt = await test_db.execute(
        select(RefreshSession).where(RefreshSession.id == refresh_token.id)
    )
    token = stmt.scalars().first()
    assert token.is_revoked is False
