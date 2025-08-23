from sqlalchemy import (
    Column, 
    Integer, 
    String,
    Boolean, 
    Text, 
    func,
    Numeric,
    DateTime,
    event,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from ppgc_backend.config.postgres_connection_manager import Base


class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    lease_duration = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    has_features = Column(Boolean, default=False)
    availability = Column(Text, nullable=False, default="available")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Enums
    category= Column(String, nullable=False)

    # Reverse relationship to asset feature
    features = Column(JSONB)

    area_id = Column(
        Integer,
        ForeignKey(
            'areas.id',
            name = 'fk_properties_area_id_areas',
            ondelete='RESTRICT',
        ),
        nullable = False
    )
    area = relationship(
        'Area',
        backref = 'property',
        uselist = False,
        lazy='selectin'
    )


@event.listens_for(Property, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()