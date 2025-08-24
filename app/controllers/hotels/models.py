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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property

from .enums import RoomType
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

    @hybrid_property
    def total_rooms(self):
        return len(self.rooms)


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(SQLAlchemyEnum(RoomType), nullable=False, default="single")
    price_per_night = Column(Float, nullable=False)
    max_occupancy = Column(Integer, nullable=False, default=2)

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
        uselist = False
    )

    @hybrid_property
    def available(self):
        return bool(self.booking)


@event.listens_for(Hotel, 'before_insert')
@event.listens_for(Room, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()