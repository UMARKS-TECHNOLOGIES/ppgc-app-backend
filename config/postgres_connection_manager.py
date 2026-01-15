from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from . import env_is_test
from ppgc_backend.config.settings import (
    DEBUG,
    DEV_DATABASE_URL,
    TEST_DATABASE_URL,
    PROD_DATABASE_URL,
)

Base = declarative_base()


def get_database_url() -> str:
    if env_is_test():
        return TEST_DATABASE_URL
    return DEV_DATABASE_URL if DEBUG else PROD_DATABASE_URL


DATABASE_URL = get_database_url()

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
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

def runtime_async_engine():
    database_url = get_database_url()
    return create_async_engine(
        database_url, echo=False, max_overflow=10, pool_timeout=30
    ) 

def runtime_async_session_maker():
    async_engine = runtime_async_engine()
    AsyncSessionMaker = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    ) 
    return AsyncSessionMaker