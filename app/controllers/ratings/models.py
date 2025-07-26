from ppgc_backend.config.postgres_connection_manager import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    CheckConstraint,
    DateTime,
    func,
    event,
    ForeignKey
)
from sqlalchemy.orm import relationship

class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=  True, index=True) 

    comment = Column(String, nullable=False)
    score = Column(Integer, default=0) # number of stars

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationship to Area
    area_id = Column(
        Integer,
        ForeignKey(
            'areas.id',
            name='fk_ratings_areas',
            ondelete='CASCADE',
            use_alter=True,
        )
    )
    area = relationship(
        'Area',
        lazy='selectin',
        backref='ratings',
        uselist = False
    )

        # relationship to Commenter
    commenter_id = Column(
        Integer,
        ForeignKey(
            'users.id',
            name = "fk_ratings_users",
            ondelete="CASCADE"
        ),
        nullable = False
    )
    commenter = relationship(
        "User",
        backref = "rating",
        lazy = "selectin",
        uselist = False
    )

    
    __table_args__ = (
        CheckConstraint("score <= 5", name="check_score_max"),
    )


@event.listens_for(Rating, 'before_insert')
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()