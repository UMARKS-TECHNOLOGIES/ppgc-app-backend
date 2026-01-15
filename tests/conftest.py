import os
import time
import signal
import requests
import subprocess
import pytest_asyncio
from sqlalchemy import text
from asgiref.sync import async_to_sync
from httpx import AsyncClient, ASGITransport

from ppgc_backend.app.main import app
from ppgc_backend.app.initiator import logger
from ppgc_backend.app.database import get_db
from ppgc_backend.config.postgres_connection_manager import Base, runtime_async_session_maker, runtime_async_engine


@pytest_asyncio.fixture(scope="function")
def test_env_var():
    os.environ["TEST_ENV"] = "true"
    yield
    os.environ.pop("TEST_ENV", None)


@pytest_asyncio.fixture(scope="function")
async def get_test_db__fixture(test_env_var):
    async_engine = runtime_async_engine()
    async with async_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        logger.info("***Dropped and recreated public schema")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("***Created a new Base metadata")

    async_session_maker = runtime_async_session_maker()
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client_fixture(
    get_test_db__fixture, 
):
    # overriding the client's get_db dependency
    app.dependency_overrides[get_db] = lambda: get_test_db__fixture  # Override get_db to use the test session

    # Use ASGITransport with the app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield {
            "http_client": ac, 
            "db": get_test_db__fixture,
        }


@pytest_asyncio.fixture(scope="function")
def app_subprocess(test_env_var):
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