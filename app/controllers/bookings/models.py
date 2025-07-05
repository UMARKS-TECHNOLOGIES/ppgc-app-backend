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
    event
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property


from .schemas import BookingStatus
from ppgc_backend.config.postgres_connection_manager import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    check_in = Column(DateTime(timezone=True), default=func.now())
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(SQLAlchemyEnum(BookingStatus), default=BookingStatus.pending, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    booker_id = Column(
        Integer, 
        ForeignKey(
            "users.id", 
            name="fk_bookings_user",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    booker = relationship(
        "User", 
        back_populates="bookings",
        lazy="selectin",
    )

    # Relationship to hotel
    hotel_id = Column(
        Integer, 
        ForeignKey(
            "hotels.id", 
            name="fk_bookings_hotels",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    hotel = relationship(
        "Hotel", 
        back_populates="bookings",
        lazy="selectin",
    )

    room_id = Column(
        Integer, 
        ForeignKey(
            "rooms.id", 
            name="fk_bookings_rooms",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    room = relationship(
        "Room", 
        back_populates="bookings",
        lazy='selectin',
        uselist = False
    )
    

@event.listens_for(Booking, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()