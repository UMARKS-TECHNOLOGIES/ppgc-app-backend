from sqlalchemy import (
    Column, 
    Integer, 
    String,
    func,
    Float,
    String,
    event,
    DateTime,
    ForeignKey, 
)
from sqlalchemy.orm import relationship

from ppgc_backend.config.postgres_connection_manager import Base


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    amount = Column(Float, nullable=False)
    interest_rate = Column(Float, default=2.0, nullable=False)  # 2% per month
    status = Column(String, default="active")  # active, completed
    duration = Column(Integer, nullable=False) # days
    # dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_investments_users",
            ondelete="CASCADE",
        ), 
        nullable=False
    )
    user = relationship(
        "User",
        backref = "investments",
        lazy = 'selectin',
        uselist=False
    )

@event.listens_for(Investment, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()