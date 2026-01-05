from ppgc_backend.config.postgres_connection_manager import AsyncSessionLocal

# Dependency to get async DB session
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db