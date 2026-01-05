from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from . import get_env
from ppgc_backend.config.settings import (
    DEBUG,
    DEV_DATABASE_URL,
    TEST_DATABASE_URL,
    PROD_DATABASE_URL,
)

Base = declarative_base()


def _get_database_url() -> str:
    if get_env() == "test":
        return TEST_DATABASE_URL
    return DEV_DATABASE_URL if DEBUG else PROD_DATABASE_URL


DATABASE_URL = _get_database_url()

async_engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_size=5,           # 👈 IMPORTANT (PgBouncer-friendly)
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,    # 👈 Prevent stale connections
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_postgres_instance():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
