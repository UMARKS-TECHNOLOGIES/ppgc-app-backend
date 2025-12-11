"""
Services for token management: list sessions, revoke tokens, revoke all tokens, and query session logs.
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from .models import AccessToken, RefreshToken, SessionLog
from ppgc_backend.app.controllers.actors.models import User


async def list_user_access_tokens(db: AsyncSession, user: User) -> List[Dict]:
    """Return list of access tokens for a user."""
    result = await db.execute(select(AccessToken).where(AccessToken.user_id == user.id))
    tokens = result.scalars().all()
    return [
        {
            "id": t.id,
            "ip_address": t.ip_address,
            "user_agent": t.user_agent,
            "is_revoked": t.is_revoked,
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tokens
    ]


async def revoke_access_token(db: AsyncSession, user: User, token_id: int) -> Dict:
    """Mark an access token as revoked for the given user."""
    result = await db.execute(select(AccessToken).where(AccessToken.id == token_id, AccessToken.user_id == user.id))
    token = result.scalars().first()
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access token not found")

    if token.is_revoked:
        return {"detail": "Token already revoked"}

    token.is_revoked = True
    db.add(token)
    await db.commit()

    # update session log if exists
    stmt = await db.execute(select(SessionLog).where(SessionLog.session_token == token.token_hash))
    session_log = stmt.scalars().first()
    if session_log:
        session_log.is_active = False
        session_log.logout_time = datetime.now(timezone.utc)
        db.add(session_log)
        await db.commit()

    return {"detail": "Access token revoked"}


async def revoke_refresh_token(db: AsyncSession, user: User, token_id: int) -> Dict:
    """Mark a refresh token as revoked for the given user."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.id == token_id, RefreshToken.user_id == user.id))
    token = result.scalars().first()
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found")

    if token.is_revoked:
        return {"detail": "Refresh token already revoked"}

    token.is_revoked = True
    db.add(token)
    await db.commit()

    return {"detail": "Refresh token revoked"}


async def revoke_all_user_tokens(db: AsyncSession, user: User) -> Dict:
    """Revoke all access and refresh tokens for the user and mark sessions inactive."""
    # Revoke access tokens
    result = await db.execute(select(AccessToken).where(AccessToken.user_id == user.id))
    access_tokens = result.scalars().all()
    for t in access_tokens:
        t.is_revoked = True
        db.add(t)

    # Revoke refresh tokens
    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
    refresh_tokens = result.scalars().all()
    for rt in refresh_tokens:
        rt.is_revoked = True
        db.add(rt)

    # Update session logs
    result = await db.execute(select(SessionLog).where(SessionLog.user_id == user.id, SessionLog.is_active == True))
    active_logs = result.scalars().all()
    now = datetime.now(timezone.utc)
    for log in active_logs:
        log.is_active = False
        log.logout_time = now
        db.add(log)

    await db.commit()

    return {"detail": "All tokens revoked and sessions terminated"}


async def get_session_logs(db: AsyncSession, user: User, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Fetch session logs for a user with pagination."""
    result = await db.execute(
        select(SessionLog)
        .where(SessionLog.user_id == user.id)
        .order_by(SessionLog.login_time.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "session_token": l.session_token,
            "login_time": l.login_time.isoformat() if l.login_time else None,
            "logout_time": l.logout_time.isoformat() if l.logout_time else None,
            "is_active": l.is_active,
        }
        for l in logs
    ]
