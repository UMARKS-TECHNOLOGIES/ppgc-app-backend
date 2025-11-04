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
    Enum as SQLAlchemyEnum
)
from datetime import timedelta
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .tools import compute_roi
from .enums import InvestmentStatus
from ppgc_backend.config.postgres_connection_manager import Base

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    amount = Column(Float, nullable=False)
    interest_rate = Column(Float, default=2.0, nullable=False)  # 2% per month
    status = Column(SQLAlchemyEnum(InvestmentStatus, name="investment_status"), default = InvestmentStatus.active, nullable=False)  # active, completed
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

    trx_id = Column(
        Integer, 
        ForeignKey(
            "transactions.id",
            name="fk_investments_trx_id_transactions",
            ondelete="RESTRICT"
        ), 
        nullable=False
    )
    trx = relationship(
        "Transaction", 
        backref="investment",
        lazy = 'selectin',
        uselist=False,
    )

    @hybrid_property
    def roi(self):
        return compute_roi(self)
    
    @hybrid_property
    def maturity_time(self):
        return self.created_at + timedelta(days=self.duration)

@event.listens_for(Investment, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()