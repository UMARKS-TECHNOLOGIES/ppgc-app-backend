from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from ppgc_backend.config.postgres_connection_manager import Base

class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, 
        ForeignKey(
            "users.id",
            name="fk_refresh_sessions_user_id_user",
            ondelete="CASCADE",
        ),
        nullable=False
    )
    user = relationship(
        'User',
        backref='refresh_session',
        uselist=False,
        lazy='selectin'
    )
    token_hash = Column(String)
    expires_at = Column(DateTime(timezone=True))
    user_agent = Column(String)
    ip_address = Column(String)
    last_used_at = Column(DateTime, nullable=True)