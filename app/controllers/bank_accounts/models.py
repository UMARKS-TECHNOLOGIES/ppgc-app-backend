from sqlalchemy import (
    Column, 
    Integer, 
    String,
    ForeignKey, 
)
from sqlalchemy.orm import relationship

from ppgc_backend.config.postgres_connection_manager import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(20), nullable=False, unique=True)
    account_name = Column(String(100), nullable=False)
    bank_name = Column(String(100), nullable=False)
    bank_code = Column(String(20), nullable=True)  # Optional: useful for integrations
    currency = Column(String(10), default="NGN")  # e.g. NGN, USD

    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id", 
            name = "fk_bank_accounts_users",
            ondelete="CASCADE"
        ), 
        nullable=False
    )
    user = relationship(
        "User", 
        lazy = "selectin",
        backref="bank_accounts",
        uselist=False
    )
