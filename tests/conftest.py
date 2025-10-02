import os
import time
import signal
import requests
import subprocess
import pytest_asyncio
from sqlalchemy import text
from asgiref.sync import async_to_sync
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from ppgc_backend.app.main import app
from ppgc_backend.app.database import get_db
from ppgc_backend.config.settings import (
    TEST_DATABASE_URL, 
)
from ppgc_backend.config.postgres_connection_manager import Base, get_postgres_instance


@pytest_asyncio.fixture
def test_env_var():
    os.environ["TEST_ENV"] = "true"
    yield
    os.environ.pop("TEST_ENV", None)

async def drop_and_create_metadata():
    # initialize a test engine and store its reference
    async_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    # Create a clean database if it's a test environment
    async with async_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        print("***Dropped and recreated public schema")
        await conn.run_sync(Base.metadata.create_all)
        print("***Created a new Base metadata")


@pytest_asyncio.fixture(scope="function")
async def get_test_db__fixture(test_env_var):
    await drop_and_create_metadata()
    async with get_postgres_instance() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client_fixture(
    get_test_db__fixture, 
):
    async for test_db in get_test_db__fixture:
        break

    # overriding the client's get_db dependency
    app.dependency_overrides[get_db] = lambda: test_db  # Override get_db to use the test session

    # Use ASGITransport with the app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield {
            "http_client": ac, 
            "db": test_db,
        }


@pytest_asyncio.fixture(scope="function")
def app_subprocess(test_env_var):
    # refresh database metadata
    async_to_sync(drop_and_create_metadata)()
    
    # On Windows, use creationflags to create a new process group
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    app = subprocess.Popen(
        [
            "uvicorn", "app.main:app", "--port",
            "8000",
        ],
        creationflags=creationflags
    )

    # Give time to start
    for _ in range(20):
        try:
            requests.get(f'http://localhost:8000/?session={int(time.time())}')
            break
        except Exception:
            time.sleep(1)  # ←
    
    yield

    # Graceful shutdown
    app.send_signal(signal.CTRL_BREAK_EVENT)

    app.wait()