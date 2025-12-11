"""
Savings models for tracking daily savings and financial activities.
"""
from sqlalchemy.orm import relationship
from ppgc_backend.app.models import Base
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, func


class DailySavings(Base):
    """
    Model for tracking daily savings and balance.
    """
    __tablename__ = "daily_savings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_daily_savings_user_id_users",
            use_alter=True,
            ondelete="CASCADE",
        ), 
        nullable=False
    )
    user = relationship(
        "User", 
        backref="daily_savings",
        lazy="selectin",
    )