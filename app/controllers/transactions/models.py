import sqlalchemy as sa
from sqlalchemy import (
    func,
    Float,
    String,
    Column, 
    Integer, 
    DateTime,
    ForeignKey, 
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .enums import TRXType
from ppgc_backend.config.postgres_connection_manager import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    name = Column(String, nullable=False)
    trx_type = Column(SQLAlchemyEnum(TRXType, name="transaction_type"), nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    trx_id = Column(String)
    __table_args__ = (
        sa.UniqueConstraint("trx_id", name="uq_transactions_trx_id"),
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


    @hybrid_property
    def goal_name(self):
        return self.name
