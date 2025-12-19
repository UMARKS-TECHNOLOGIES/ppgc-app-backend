# main.py
from fastapi import (
    Depends, 
    FastAPI,
    APIRouter, 
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


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
from fastapi import Request
from contextlib import asynccontextmanager
from ppgc_backend.app.controllers.auth import routes as auth_routes
from ppgc_backend.app.controllers.logs import routes as logs_routes
from ppgc_backend.app.controllers.hotels import routes as hotel_routes
from ppgc_backend.app.controllers.auth.services import initialize_admin
from ppgc_backend.app.controllers.savings import routes as savings_routes
from ppgc_backend.app.controllers.bookings import routes as bookings_routes
from ppgc_backend.app.controllers.settings import routes as settings_routes
from ppgc_backend.app.controllers.inspection import routes as inspection_routes
from ppgc_backend.app.controllers.properties import routes as properties_routes
from ppgc_backend.app.controllers.investments import routes as investments_routes
from ppgc_backend.app.controllers.transactions import routes as transaction_routes
from ppgc_backend.app.controllers.bank_accounts import routes as bank_accounts_routes
from ppgc_backend.app.controllers.two_factor_auth import routes as two_factor_auth_routes
from ppgc_backend.app.controllers.activity_logging import routes as activity_logging_routes
from ppgc_backend.app.controllers.activity_logging.middleware import ActivityLoggerMiddleware
from ppgc_backend.config.postgres_connection_manager import get_postgres_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with get_postgres_instance() as session:
        await initialize_admin(session)
    yield  

    # Application runs here
    # Shutdown logic (if needed)
    # e.g., await redis_client.close()

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# proxy middleware
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts="*"
)
# Logger middleware
app.add_middleware(ActivityLoggerMiddleware)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

home_router = APIRouter()

environment = 'DEVELOPMENT' if DEBUG else 'PRODUCTION'

@home_router.get("/")
def read_root():
    return {
        "message": "Hello, World!",
        "environment": environment
    }

@home_router.get("/debug/scheme/")
async def debug_scheme(request: Request):
    return {
        "scheme": request.url.scheme,
        "headers": dict(request.headers),
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
app.include_router(logs_routes.router)
app.include_router(auth_routes.router)
app.include_router(hotel_routes.router)
app.include_router(savings_routes.router)
app.include_router(bookings_routes.router)
app.include_router(settings_routes.router)
app.include_router(inspection_routes.router)
app.include_router(properties_routes.router)
app.include_router(transaction_routes.router)
app.include_router(investments_routes.router)
app.include_router(bank_accounts_routes.router)
app.include_router(two_factor_auth_routes.router)
app.include_router(activity_logging_routes.router)
# app.include_router(search.router)
if DEBUG:
    app.include_router(home_router)