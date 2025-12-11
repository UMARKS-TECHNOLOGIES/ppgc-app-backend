"""
Two-factor authentication models.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, event, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ppgc_backend.app.models import Base
from .enums import TwoFactorAuthLogAttemptType

class TwoFactorAuth(Base):
    """
    Model for storing two-factor authentication settings and secrets.
    """
    __tablename__ = "two_factor_auth"

    id = Column(Integer, primary_key=True, index=True)
    is_enabled = Column(Boolean, default=False)
    secret_key = Column(String, nullable=True)  # TOTP secret
    backup_codes = Column(String, nullable=True)  # Comma-separated backup codes
    method = Column(String, default="totp")  # totp or sms
    phone_number = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_two_factor_auth_user_id_users",
            ondelete="CASCADE",
        ), 
        nullable=False
    )
    user = relationship(
        "User",
        backref="two_factor_auth",
        lazy='selectin',
        uselist=False
    )

@event.listens_for(TwoFactorAuth, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()


class TwoFactorAuthLog(Base):
    """
    Model for logging two-factor authentication attempts.
    """
    __tablename__ = "two_factor_auth_log"

    id = Column(Integer, primary_key=True, index=True)
    attempt_type = Column(
        SQLAlchemyEnum(TwoFactorAuthLogAttemptType, name="two_factor_log_attempt_type"), 
        nullable=False
    )  # setup, verify, failed_attempt
    success = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_two_factor_auth_log_user_id_user",
            ondelete="CASCADE",
            use_alter=True
        ), 
        nullable=False
    )
    user = relationship(
        "User",
        backref="two_factor_auth_log",
        lazy='selectin',
        uselist=False
    )
