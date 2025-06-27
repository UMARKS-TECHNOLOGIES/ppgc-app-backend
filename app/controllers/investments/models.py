from sqlalchemy import (
    Column, 
    Integer, 
    String,
    ForeignKey, 
    func,
    DateTime,
    event,
    ARRAY,
    Float,
    String,
)
from sqlalchemy.orm import relationship


from ppgc_backend.app.database import Base


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
        back_populates = "investments",
        lazy = 'selectin',
        uselist=False
    )

    # Relationship
    transactions = relationship(
        "InvestmentTransaction", 
        back_populates="investment",
        lazy = 'selectin',
    )


class InvestmentTransaction(Base):
    __tablename__ = "investment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # deposit, withdraw
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    investment_id = Column(
        Integer, 
        ForeignKey(
            "investments.id",
            name="fk_investments_transactions_investments",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    investment = relationship(
        "Investment", 
        back_populates="transactions",
        lazy = 'selectin',
    )

@event.listens_for(Investment, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()