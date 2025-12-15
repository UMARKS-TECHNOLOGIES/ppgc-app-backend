"""
Schemas for activity logging endpoints.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .models import ActivityStatusChoice


class ActivityLogCreateSchema(BaseModel):
    """Schema for creating activity logs."""
    action: str = Field(..., description="Action name (e.g., 'POST /auth/signin')")
    status: ActivityStatusChoice = Field(default=ActivityStatusChoice.pending, description="Activity status")
    description: Optional[str] = Field(None, description="Additional details about the activity")
    method: Optional[str] = Field(None, description="HTTP method")
    endpoint: Optional[str] = Field(None, description="API endpoint path")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    request_body: Optional[str] = Field(None, description="Sanitized request payload")
    response_status_code: Optional[int] = Field(None, description="HTTP response status code")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class ActivityLogResponseSchema(BaseModel):
    """Schema for activity log responses."""
    id: int
    user_id: int
    session_id: Optional[int] = None
    action: str
    status: ActivityStatusChoice
    description: Optional[str] = None
    method: Optional[str] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_body: Optional[str] = None
    response_status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogListResponseSchema(BaseModel):
    """Schema for paginated activity logs."""
    total: int = Field(..., description="Total number of activity logs")
    count: int = Field(..., description="Number of logs in this response")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    items: List[ActivityLogResponseSchema] = Field(..., description="List of activity logs")

    model_config = ConfigDict(from_attributes=True)


class ActivityStatisticsSchema(BaseModel):
    """Schema for activity statistics."""
    total_activities: int = Field(..., description="Total number of activities")
    successful: int = Field(..., description="Count of successful activities")
    failed: int = Field(..., description="Count of failed activities")
    pending: int = Field(..., description="Count of pending activities")
    error: int = Field(..., description="Count of error activities")
    most_common_action: Optional[str] = Field(None, description="Most frequently logged action")
    success_rate: float = Field(..., description="Success rate as percentage (0-100)")

    model_config = ConfigDict(from_attributes=True)
