import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_debug_scheme(client_fixture):
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj['http_client']
        break

    scheme = "https"
    headers = {
        "X-Forwarded-Proto": scheme
    }
    resp = await httpx_client.get(f"/debug/scheme/", headers=headers)
    assert resp.status_code == 200
    json_resp = resp.json()
    assert json_resp['scheme'] == scheme