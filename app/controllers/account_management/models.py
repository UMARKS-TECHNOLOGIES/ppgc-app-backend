"""
Account management models for account deactivation and settings.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ppgc_backend.app.models import Base


class AccountDeactivation(Base):
    """
    Model for tracking account deactivations.
    """
    __tablename__ = "account_deactivation"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False, index=True)
    is_deactivated = Column(Boolean, default=False)
    deactivation_reason = Column(String, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    reactivation_token = Column(String, nullable=True, unique=True)
    token_expires_at = Column(DateTime, nullable=True)
    can_reactivate_until = Column(DateTime, nullable=True)  # Data retention period
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="account_deactivation")


class AccountSettings(Base):
    """
    Model for user account settings and preferences.
    """
    __tablename__ = "account_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    privacy_level = Column(String, default="private")  # public, friends_only, private
    show_activity = Column(Boolean, default=False)
    allow_messages = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="account_settings")
