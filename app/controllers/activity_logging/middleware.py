import time
from fastapi import Request
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from .models import ActivityLog
from .enums import ActivityStatusChoice
from ppgc_backend.app.controllers.actors.models import User


class ActivityLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = None
        status_code = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except HTTPException as exc:
            status_code = exc.status_code
            raise

        except Exception:
            status_code = 500
            raise

        finally:
            # Only log authenticated requests
            user: User = getattr(request.state, "user", None)
            db: AsyncSession = getattr(request.state, "db", None)
            if not user and not db:
                return response

            duration_ms = int((time.time() - start_time) * 1000)

            try: 
                log = ActivityLog(
                    user_id=user.id,
                    action=f"{request.method} {request.url.path}",
                    status=(
                        ActivityStatusChoice.success
                        if status_code < 400
                        else ActivityStatusChoice.failed
                    ),
                    method=request.method,
                    endpoint=request.url.path,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    response_status_code=status_code,
                    response_time_ms=duration_ms,
                )
                db.add(log)
                await db.commit()
            except:
                # allow the original response
                pass