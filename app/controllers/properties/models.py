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
from sqlalchemy.dialects.postgresql import ARRAY

from ppgc_backend.app.model_helper import CloudImageDetail
from ppgc_backend.config.postgres_connection_manager import Base

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    description = Column(Text, nullable=True)
    availability = Column(Text, nullable=False, default="available")
    type = Column(String, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # One-to-one relationship for cover image (no cascade)
    cover_image_id = Column(
        Integer, 
        ForeignKey(
            'cloud_image_details.id', 
            name='fk_properties_cover_image_id_cloud_image_details', 
            use_alter=True, 
            ondelete='SET NULL'
        ), 
        nullable=True
    )
    cover_image = relationship(
        'CloudImageDetail', 
        uselist=False, # explicitly tell SQLAlchemy it's a one-to-one
        foreign_keys=[cover_image_id], 
        post_update=True,
        lazy="selectin",  # Ensures relationship loads in async contexts
    )

    # Many other images
    other_images = relationship(
        "CloudImageDetail",
        backref="property",   # adds .property on CloudImageDetail
        foreign_keys=[CloudImageDetail.property_id],
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Reverse relationship to asset feature
    features = Column(ARRAY(String), default=list)

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