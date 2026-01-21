from sqlalchemy import (
    Column,
    String,
    Integer,
    CheckConstraint,
    DateTime,
    func,
    event,
    ForeignKey,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship


from .enums import RatingType
from ppgc_backend.config.postgres_connection_manager import Base

class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, index=True)

    comment = Column(String, nullable=False)
    score = Column(Integer, default=0)  # number of stars (1-5)

    # Discriminator column for polymorphic rating (hotel, room, property)
    rateable_type = Column(
        SQLAlchemyEnum(RatingType, name='rating_type_enum'),
        nullable=False,
        index=True
    )

    # Generic foreign key to the rateable asset
    rateable_id = Column(Integer, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to commenter (rater)
    commenter_id = Column(
        Integer,
        ForeignKey(
            'users.id',
            name="fk_ratings_commenter_id_users",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    commenter = relationship(
        "User",
        backref="ratings",
        lazy="selectin",
        uselist=False
    )

    # Specific relationships for each asset type
    hotel_id = Column(
        Integer,
        ForeignKey(
            'hotels.id',
            name='fk_ratings_hotel_id',
            ondelete='CASCADE',
            use_alter=True,
        ),
        nullable=True
    )
    hotel = relationship(
        'Hotel',
        lazy='selectin',
        backref='ratings',
        uselist=False,
        foreign_keys=[hotel_id]
    )

    room_id = Column(
        Integer,
        ForeignKey(
            'rooms.id',
            name='fk_ratings_room_id',
            ondelete='CASCADE',
            use_alter=True,
        ),
        nullable=True
    )
    room = relationship(
        'Room',
        lazy='selectin',
        backref='ratings',
        uselist=False,
        foreign_keys=[room_id]
    )

    property_id = Column(
        Integer,
        ForeignKey(
            'properties.id',
            name='fk_ratings_property_id',
            ondelete='CASCADE',
            use_alter=True,
        ),
        nullable=True
    )
    property = relationship(
        'Property',
        lazy='selectin',
        backref='ratings',
        uselist=False,
        foreign_keys=[property_id]
    )

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 5", name="check_score_range"),
    )


@event.listens_for(Rating, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()