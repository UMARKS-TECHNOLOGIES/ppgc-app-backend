"""
Token management models for refresh tokens and session management.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ppgc_backend.app.models import Base


class RefreshSession():
    """
    Model for storing refresh tokens.
    """
    pass


class AccessToken():
    """
    Model for tracking access tokens and their lifecycle.
    """
    pass


class SessionLog():
    """
    Model for logging user sessions.
    """
    pass
