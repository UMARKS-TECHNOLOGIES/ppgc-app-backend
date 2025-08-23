from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Date, Time, Integer, ForeignKey, Enum as SQLAlchemyEnum

from .enums import InspectionStatus
from ppgc_backend.config.postgres_connection_manager import Base

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    call_number = Column(String, nullable=False)
    date_of_inspection = Column(Date, nullable=False)
    time_of_inspection = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(
        SQLAlchemyEnum(InspectionStatus, name="inspection_status_choice"),
        default=InspectionStatus.pending
    )

    # Relationships (nullable)
    requester_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name='fk_inspections_users',
            ondelete='CASCADE'
        ), 
        nullable=True
    )
    requester = relationship(
        "User", 
        backref="inspections", 
        lazy="selectin",
        uselist=False
    )

    property_id = Column(
        Integer, 
        ForeignKey(
            "properties.id",
            name="fk_inspections_properties",
            ondelete="SET NULL"
        ), 
    )
    property = relationship(
        "Property", 
        backref="inspections", 
        lazy="selectin",
        uselist=False,
    )
