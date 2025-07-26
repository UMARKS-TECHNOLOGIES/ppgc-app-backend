# main.py
from fastapi import (
    APIRouter, 
    Depends, 
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware


from ppgc_backend.app.controllers.auth import routes as auth_routes
from ppgc_backend.app.database import (
    get_db,
)
# from ppgc_backend.app.routers import (
#     activity,
#     search,
#     settings,
#     roi,
# )
from ppgc_backend.app.initiator import (
    app, 
)
from ppgc_backend.config.settings import (
    environment,
    CORS_ORIGINS
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include celery app

home_router = APIRouter()

@home_router.get("/")
def read_root():
    return {
        "message": "Hello, World!",
        "environment": environment
    }


@home_router.get("/test-database")
async def test_database(
    session: AsyncSession = Depends(get_db),
):
    """
    Test database connectivity by running a simple query.
    """
    try:
        # Test query (replace 'your_table_name' with a real table if needed)
        result = await session.execute(text("SELECT 1"))
        value = result.scalar()  # Fetch the first scalar result

        return {
            "database_connected": True,
            "test_value": value,
            "environment": environment,
        }
    except Exception as e:
        # Log and return error details
        return {
            "database_connected": False,
            "error": str(e),
            "environment": environment,
        }

# Include routers
app.include_router(auth_routes.router)
# app.include_router(activity.router)
# app.include_router(search.router)
# app.include_router(settings.router)
# app.include_router(roi.router)
# app.include_router(home_router)