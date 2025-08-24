from sqlalchemy import (
    func,
    Enum as SQLAlchemyEnum, 
    Float, 
    Column, 
    Integer, 
    DateTime,
    ForeignKey, 
    event
)
from sqlalchemy.orm import relationship


from .enums import BookingStatus
from ppgc_backend.config.postgres_connection_manager import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    check_in = Column(DateTime(timezone=True), default=func.now())
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(SQLAlchemyEnum(BookingStatus), default=BookingStatus.pending, nullable=False)

    created_at = Column(DateTime(timezone=True), default=func.now())
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
        backref="bookings",
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
        back_populates="booking",
        lazy='selectin',
        uselist = False
    )
    

@event.listens_for(Booking, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()