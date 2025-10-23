import sqlalchemy as sa
from sqlalchemy import (
    func,
    Enum as SQLAlchemyEnum, 
    Float, 
    String, 
    Column, 
    Integer, 
    DateTime,
    ForeignKey, 
    event
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from .enums import RoomType, RoomStatus
from ppgc_backend.config.postgres_connection_manager import Base
from ppgc_backend.app.controllers.ratings.utils import AggregateRatingAClass


class Hotel(AggregateRatingAClass):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    cover_image = Column(JSONB, nullable=False, default=dict) # {secure_url: str, public_id: str}
    other_images = Column(JSONB) #[{secure_url: str, public_id: str},]
    
    rooms = relationship(
        "Room", 
        back_populates="hotel", 
        cascade="all, delete-orphan",
        lazy='selectin'
    )

    area_id = Column(
        Integer,
        ForeignKey(
            "areas.id", 
            name="fk_hotels_areas",
            ondelete="CASCADE"
        ),  
        nullable=False,
    ) 
    area = relationship(
        "Area",
        backref="hotel",
        lazy="selectin",
        uselist=False # one-to-one relationship
    )

    # New: Manager & Receptionist
    manager_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_hotels_manager_id", ondelete="CASCADE"),
        nullable=False
    )
    manager = relationship(
        "User",
        backref="managed_hotels",
        foreign_keys=[manager_id],
        lazy="selectin"
    )

    receptionist_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_hotels_receptionist_id", ondelete="SET NULL"),
        nullable=True
    )
    receptionist = relationship(
        "User",
        backref="receptionist_hotels",
        foreign_keys=[receptionist_id],
        lazy="selectin"
    )

    invite_token = Column(String(255), nullable=True, unique=True)  # one-time link code
    invite_token_expiry = Column(DateTime(timezone=True), nullable=True)

    @hybrid_property
    def total_rooms(self):
        return len(self.rooms)


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(SQLAlchemyEnum(RoomType), nullable=False, default="single")
    room_number = Column(String(50), nullable=True)  # e.g. "A101"
    price_per_night = Column(Float, nullable=False)
    max_occupancy = Column(Integer, nullable=False, default=2)
    bed_count = Column(Integer, default=1)
    description = Column(String(500), nullable=True)
    amenities = Column(ARRAY(String), default=list)  # e.g. ["WiFi", "AC", "TV"]
    status = Column(SQLAlchemyEnum(RoomStatus), nullable=False, default=RoomStatus.available)
    cover_image = Column(JSONB, default=dict) # {secure_url: str, public_id: str}
    other_images = Column(JSONB) #[{secure_url: str, public_id: str},]

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # relationship to hotel
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

    # relationship to booking
    booking = relationship(
        "Booking", 
        back_populates="room",
        lazy="selectin",
        uselist = False,
        cascade="all, delete-orphan",
    )
 
    __table_args__ = (
        sa.UniqueConstraint("room_number", name="uq_rooms_room_number"),
    )
 
    @hybrid_property
    def available(self):
        """True if not currently booked or under maintenance."""
        return self.status == RoomStatus.available and self.booking is None


@event.listens_for(Hotel, 'before_insert')
@event.listens_for(Room, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()