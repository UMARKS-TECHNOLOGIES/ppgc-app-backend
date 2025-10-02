# main.py
from fastapi import (
    Depends, 
    FastAPI,
    APIRouter, 
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware


from contextlib import asynccontextmanager
from ppgc_backend.app.controllers.auth import routes as auth_routes
from ppgc_backend.app.controllers.hotels import routes as hotel_routes
from ppgc_backend.app.controllers.auth.services import initialize_admin
from ppgc_backend.app.controllers.bookings import routes as bookings_routes
from ppgc_backend.app.controllers.inspection import routes as inspection_routes
from ppgc_backend.app.controllers.properties import routes as properties_routes
from ppgc_backend.app.database import (
    get_db,
)
from ppgc_backend.app.initiator import (
    app, 
)
from ppgc_backend.config.settings import (
    DEBUG,
    CORS_ORIGINS
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await initialize_admin()
    yield  
    # Application runs here
    # Shutdown logic (if needed)
    # e.g., await redis_client.close()

app = FastAPI(lifespan=lifespan)


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

environment = 'DEVELOPMENT' if DEBUG else 'PRODUCTION'

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
app.include_router(hotel_routes.router)
app.include_router(bookings_routes.router)
app.include_router(inspection_routes.router)
app.include_router(properties_routes.router)
# app.include_router(activity.router)
# app.include_router(search.router)
# app.include_router(settings.router)
# app.include_router(roi.router)
if DEBUG:
    app.include_router(home_router)