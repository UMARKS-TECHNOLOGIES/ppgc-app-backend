from sqlalchemy import (
    func,
    Enum as SQLAlchemyEnum, 
    Float, 
    Column, 
    Integer, 
    DateTime,
    ForeignKey, 
    String,
    Text,
    event,
    Index,
    and_
)
from sqlalchemy.orm import relationship


from .enums import BookingStatus
from ppgc_backend.config.postgres_connection_manager import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    # Guest information
    guest_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    # Booking dates
    check_in = Column(DateTime(timezone=True), nullable=False)
    check_out = Column(DateTime(timezone=True), nullable=False)

    # Pricing information
    price_per_night = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, nullable=False, default=0.0)
    balance_payment = Column(Float, nullable=False)
    
    # Legacy field for compatibility
    total_price = Column(Float, nullable=False)
    
    # Booking status
    status = Column(SQLAlchemyEnum(BookingStatus), default=BookingStatus.pending, nullable=False)
    guests = Column(Integer, nullable=False, default=1)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())
    
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
        nullable=False,
        index=True
    )
    room = relationship(
        "Room", 
        back_populates="booking",
        lazy='selectin',
        uselist = False
    )

    hotel_id = Column(
        Integer,
        ForeignKey(
            "hotels.id",
            name="fk_bookings_hotels",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )
    hotel = relationship(
        "Hotel",
        backref="bookings",
        lazy='selectin'
    )

    total_number_of_days = Column(Integer, nullable=False, default=1)
 
    # Composite index for room uniqueness during date range
    __table_args__ = (
        Index('ix_bookings_room_check_in_check_out', 'room_id', 'check_in', 'check_out'),
    )
    

@event.listens_for(Booking, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()
    target.created_at = func.now()