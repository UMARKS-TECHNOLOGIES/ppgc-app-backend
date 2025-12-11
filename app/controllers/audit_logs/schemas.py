"""
Audit logs schemas.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogSchema(BaseModel):
    """Audit log response schema"""
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationLogSchema(BaseModel):
    """Notification log response schema"""
    id: int
    user_id: int
    notification_type: str
    subject: Optional[str] = None
    message: str
    is_read: bool
    is_sent: bool
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogSchema(BaseModel):
    """Activity log response schema"""
    id: int
    user_id: int
    activity_type: str
    duration_seconds: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogsFilterRequest(BaseModel):
    """Request to filter audit logs"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 50


class NotificationLogFilterRequest(BaseModel):
    """Request to filter notification logs"""
    user_id: Optional[int] = None
    notification_type: Optional[str] = None
    is_read: Optional[bool] = None
    is_sent: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
