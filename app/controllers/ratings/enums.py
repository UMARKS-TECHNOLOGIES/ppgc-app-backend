from enum import Enum 

class RatingType(Enum):
    """Enum for types of rateable assets"""
    hotel = "hotel"
    room = "room"
    property = "property"