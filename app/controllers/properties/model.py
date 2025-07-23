from sqlalchemy import (
    Column, 
    Integer, 
    String,
    ForeignKey, 
    Date, 
    Boolean, 
    JSON, 
    Text, 
    Table,
    Enum as SQLAlchemyEnum, 
    func,
    Numeric,
    DateTime,
    event,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base


from ppgc_backend.config.postgres_connection_manager import Base


Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    country = Column(String, nullable=False)
    address = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    amount = Column(Numeric, nullable=False)
    lease_duration = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    has_features = Column(Boolean, default=False)
    availability = Column(Text, nullable=False, default="available")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Enums
    #category= Column(SQLAlchemyEnum(AssetCategoryChoice, name='asset_category_choice'), nullable=True)
    category= Column(String, nullable=False)

    # Reverse relationship to asset feature
    features = Column(JSONB)

@event.listens_for(Property, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()