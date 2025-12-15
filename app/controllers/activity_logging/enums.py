from enum import Enum

class ActivityStatusChoice(str, Enum):
    """Enum for activity status."""
    success = "success"
    failed = "failed"
    pending = "pending"
    error = "error"