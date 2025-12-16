"""
Activity logging models for tracking user actions and request details.
"""

from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum as SqlalchemyEnum, func


from .enums import ActivityStatusChoice
from ppgc_backend.config.postgres_connection_manager import Base

class ActivityLog(Base):
    """
    Model for logging user activities tied to sessions.
    Tracks actions, request details, and their status.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Activity details
    action = Column(String(255), nullable=False, index=True)  # e.g., "POST /auth/signin", "GET /settings"
    status = Column(
        SqlalchemyEnum(ActivityStatusChoice, name='activity_status_choice'),
        default=ActivityStatusChoice.pending,
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=True)  # Additional details about the activity
    
    # Request details
    method = Column(String(10), nullable=True)  # HTTP method (GET, POST, PUT, DELETE, etc.)
    endpoint = Column(String(500), nullable=True)  # API endpoint path
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    request_body = Column(Text, nullable=True)  # Sanitized request payload (no sensitive data)
    response_status_code = Column(Integer, nullable=True)  # HTTP response status
    response_time_ms = Column(Integer, nullable=True)  # Time taken in milliseconds
    activity_type = Column(String, nullable=True)  # view, create, update, delete, search, etc.
    # Timestamps
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    
    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_activity_logs_user_id_users",
            ondelete="CASCADE",
        ),
        nullable=False, 
        index=True
    )
    user = relationship(
        "User", 
        backref="activity_logs",
        uselist=False,
        lazy="selectin"
    )

    __table_args__ = (
        # Index on user_id and timestamp for efficient queries
        # Index on status for filtering
    )
