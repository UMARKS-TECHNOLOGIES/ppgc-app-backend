"""
Token management models for refresh tokens and session management.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ppgc_backend.app.models import Base


class RefreshToken(Base):
    """
    Model for storing refresh tokens.
    """
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")


class AccessToken(Base):
    """
    Model for tracking access tokens and their lifecycle.
    """
    __tablename__ = "access_token"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="access_tokens")


class SessionLog(Base):
    """
    Model for logging user sessions.
    """
    __tablename__ = "session_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    session_token = Column(String, nullable=True)
    login_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    logout_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
