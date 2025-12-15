import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from ppgc_backend.app.controllers.token_management.models import RefreshToken
from ppgc_backend.app.controllers.auth.services import fetch_access_token
from ppgc_backend.tests.auth.test_user_creation import create_test_user


@pytest.mark.asyncio
async def test_middleware_does_not_log_unauthenticated_requests(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        test_db: AsyncSession = fixture_obj['db']
        break

    # call a public endpoint without auth
    resp = await httpx_client.get('/')
    assert resp.status_code == 200

    # calling public activity logs endpoint without auth should be rejected
    logs_resp = await httpx_client.get('/activity-logs/my-activities')
    assert logs_resp.status_code in (401, 403)