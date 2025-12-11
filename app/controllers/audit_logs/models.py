"""
Audit logs models for tracking user activities and system events.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ppgc_backend.app.models import Base


class AuditLog(Base):
    """
    Model for comprehensive audit logging of user activities.
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)  # login, logout, password_change, profile_update, etc.
    resource_type = Column(String, nullable=True)  # user, property, settings, etc.
    resource_id = Column(String, nullable=True)  # ID of the affected resource
    description = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True, index=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, default="success")  # success, failed, pending
    changes = Column(Text, nullable=True)  # JSON format of what changed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="audit_logs")


class NotificationLog(Base):
    """
    Model for tracking notifications sent to users.
    """
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    notification_type = Column(String, nullable=False)  # email, push, in_app
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    recipient_email = Column(String, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="notification_logs")


class ActivityLog(Base):
    """
    Model for tracking user activity patterns and analytics.
    """
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    activity_type = Column(String, nullable=False)  # view, create, update, delete, search, etc.
    duration_seconds = Column(Integer, nullable=True)  # How long the activity took
    details = Column(Text, nullable=True)  # JSON format additional details
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="activity_logs")
