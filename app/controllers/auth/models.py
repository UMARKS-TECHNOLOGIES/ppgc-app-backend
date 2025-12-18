from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    func,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from ppgc_backend.config.postgres_connection_manager import Base
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice

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
    is_revoked = Column(Boolean, default=True)
    access_token_hash = Column(String, nullable=True)
    token_hash = Column(String)
    expires_at = Column(DateTime(timezone=True))
    user_agent = Column(String)
    ip_address = Column(String)
    last_used_at = Column(DateTime, nullable=True)


class RoleBasedToken(Base):
    """Model to store role-based invite tokens (e.g., for staff registration)"""
    __tablename__ = "role_based_tokens"

    id = Column(Integer, primary_key=True)
    role = Column(
        SQLAlchemyEnum(UserRoleChoice, name='role_choice_enum'),
        nullable=False
    )
    token = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=True, index=True)  # Optional: target email
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional: track who created the token
    created_by_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_role_based_tokens_created_by",
            ondelete="SET NULL"
        ),
        nullable=True
    )
    created_by = relationship(
        'User',
        foreign_keys=[created_by_id],
        lazy='selectin',
        uselist=False
    )