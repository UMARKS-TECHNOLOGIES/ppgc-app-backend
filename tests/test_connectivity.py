import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from ppgc_backend.app.main import app

@pytest.mark.asyncio
async def test_db_connectivity(
    get_test_db__fixture: AsyncSession
):
    async for test_db in get_test_db__fixture:
        assert isinstance(test_db, AsyncSession)


@pytest.mark.asyncio
async def test_client_connectivity(client_fixture):
    # get the yield client objects
    async for fixture_obj in client_fixture:
        httpx_client: AsyncClient = fixture_obj["http_client"]
        test_db: AsyncSession = fixture_obj['db']

    # database assertion
    assert isinstance(test_db, AsyncSession)

    # assertions for client
    assert isinstance(httpx_client, AsyncClient)
    # Making a request to a URL
    url = "/"
    response = await httpx_client.get(url)

    # Checking the response
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello, World!",
        "environment": "development"
    }

    # Making a request to a URL
    url = "/test-database"
    response = await httpx_client.get(url)

    # Checking the response
    assert response.status_code == 200
    assert response.json().get("database_connected")


# Adding a pseudo endpoint to the FastAPI app for testing
@app.get("/pseudo-url")
async def pseudo_url():
    return {"message": "This is a pseudo endpoint"}
