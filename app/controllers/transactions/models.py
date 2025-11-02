from sqlalchemy import (
    func,
    Float,
    Column, 
    Integer, 
    DateTime,
    ForeignKey, 
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship

from .enums import TRXType
from ppgc_backend.config.postgres_connection_manager import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(SQLAlchemyEnum(TRXType, name="transaction_type"), nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    investment_id = Column(
        Integer, 
        ForeignKey(
            "investments.id",
            name="fk_transactions_investments",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    investment = relationship(
        "Investment", 
        backref="transactions",
        lazy = 'selectin',
    )

    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_transactions_user_id_users",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    user = relationship(
        "User", 
        backref="transactions",
        lazy = 'selectin',
    )