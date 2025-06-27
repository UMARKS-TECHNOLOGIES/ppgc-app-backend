from sqlalchemy import (
    func,
    Enum as SQLAlchemyEnum, 
    Float, 
    String, 
    Column, 
    Boolean,
    Integer, 
    DateTime,
    ForeignKey, 
)
from datetime import datetime
from sqlalchemy.orm import relationship


from .enums import RoomType, BookingStatus
from ppgc_backend.config.postgres_connection_manager import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    star_rating = Column(Integer, nullable=False, default=3)  # 1 to 5 stars
    total_rooms = Column(Integer, nullable=False, default=0)
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    rooms = relationship(
        "Room", 
        back_populates="hotel", 
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    bookings = relationship(
        "Booking", 
        back_populates="hotel",
        lazy='selectin'
    )


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(
        Integer, 
        ForeignKey(
            "hotels.id", 
            name="fk_rooms_hotels",
            ondelete="CASCADE",
        ), 
        nullable=False
    )
    hotel = relationship(
        "Hotel", 
        back_populates="rooms",
        lazy="selectin"
    )
    room_type = Column(SQLAlchemyEnum(RoomType), nullable=False, default="single")
    price_per_night = Column(Float, nullable=False)
    availability = Column(Boolean, default=True, nullable=False)
    max_occupancy = Column(Integer, nullable=False, default=2)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    bookings = relationship(
        "Booking", 
        back_populates="room",
        lazy="selectin"
    )

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(SQLAlchemyEnum(BookingStatus), default=BookingStatus.pending, nullable=False)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id", 
            name="fk_bookings_user",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    # Relationships
    user = relationship(
        "User", 
        back_populates="bookings",
        lazy="selectin",
    )
    hotel = relationship(
        "Hotel", 
        back_populates="bookings",
        lazy="selectin",
    )
    room = relationship("Room", back_populates="bookings")