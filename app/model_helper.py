from sqlalchemy import (
    Column, 
    Integer, 
    String,
    ForeignKey,
)

from ppgc_backend.config.postgres_connection_manager import Base


class CloudImageDetail(Base):  # Inherit the abstract base
    __tablename__ = 'cloud_image_details'

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, nullable=False)
    secure_url = Column(String, nullable=False)

    # FK for linking other images to a property
    property_id = Column(
        Integer,
        ForeignKey(
            "properties.id", 
            name='fk_cloud_image_detials_property_id_properties',
            ondelete="CASCADE"
        ),
        nullable=True
    )
