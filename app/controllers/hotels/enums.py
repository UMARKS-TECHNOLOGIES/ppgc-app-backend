import enum

class RoomType(str, enum.Enum):
    single = "single"
    double = "double"
    suite = "suite"
    deluxe = "deluxe"
    family = "family"

class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"

class RoomStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"