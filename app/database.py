from ppgc_backend.app.db.postgres import get_postgres_instance

# Dependency to get async DB session
async def get_db():
    async with get_postgres_instance() as db:
        yield db
