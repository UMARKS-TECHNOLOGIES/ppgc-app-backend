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


def get_async_session():
    env_is_test = get_env() == 'test'
    database_url = TEST_DATABASE_URL if env_is_test else (DEV_DATABASE_URL if DEBUG else PROD_DATABASE_URL)

    async_engine = create_async_engine(database_url, echo=False) # create engine (it manages a connection pool internally)

    SessionMaker = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    ) 

    return SessionMaker

@asynccontextmanager
async def get_postgres_instance():
    SessionLocal: sessionmaker = get_async_session()

    async with SessionLocal() as session:
        yield session