from enum import Enum

class InvestmentStatus(str, Enum):
    active = "active"
    completed = "completed"
    canceled = "canceled"