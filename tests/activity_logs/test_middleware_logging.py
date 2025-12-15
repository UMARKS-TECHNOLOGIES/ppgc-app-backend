import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from ppgc_backend.tests.auth import signin_and_get_test_access_token
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user, user_data


@pytest.mark.asyncio
async def test_middleware_logs_authenticated_request_for_logout(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # create user and refresh token
    _ = await create_test_user(test_db)
    access_token = await signin_and_get_test_access_token(user_data, httpx_client)

    # call logout endpoint (protected)
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await httpx_client.delete(f"/auth/logout/", headers=headers)
    assert resp.status_code == 204

    # create new access_token, query activity logs for user
    access_token = await signin_and_get_test_access_token(user_data, httpx_client)
    headers = {"Authorization": f"Bearer {access_token}"}
    logs_resp = await httpx_client.get('/activity-logs/my-activities/', headers=headers)
    assert logs_resp.status_code == 200
    data = logs_resp.json()
    assert data['total'] >= 1
    # find logout action in items
    actions = [item['action'] for item in data['items']]
    assert any('/auth/logout' in a for a in actions)

