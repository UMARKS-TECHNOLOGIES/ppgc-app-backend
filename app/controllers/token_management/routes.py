from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.auth.services import decode_user_from_token
from ppgc_backend.app.controllers.actors.models import User
from .services import (
    list_user_access_tokens,
    revoke_access_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    get_session_logs,
)

router = APIRouter(prefix='/token-management')


@router.get('/sessions')
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """List active and historical access tokens for the authenticated user."""
    return await list_user_access_tokens(db, user)


@router.post('/revoke/access/{token_id}')
async def revoke_access(
    token_id: int = Path(..., description="ID of the access token to revoke"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """Revoke a single access token belonging to the authenticated user."""
    return await revoke_access_token(db, user, token_id)


@router.post('/revoke/refresh/{token_id}')
async def revoke_refresh(
    token_id: int = Path(..., description="ID of the refresh token to revoke"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """Revoke a single refresh token belonging to the authenticated user."""
    return await revoke_refresh_token(db, user, token_id)


@router.post('/revoke/all')
async def revoke_all(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """Revoke all tokens and end all sessions for the authenticated user."""
    return await revoke_all_user_tokens(db, user)


@router.get('/logs')
async def session_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """Fetch session logs with pagination for the authenticated user."""
    return await get_session_logs(db, user, limit=limit, offset=offset)
