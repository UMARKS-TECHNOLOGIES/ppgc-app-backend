import uuid
from sqlalchemy import (
    Column, 
    Integer, 
    String,
    Boolean, 
    JSON, 
    Enum as SQLAlchemyEnum, 
    func,
    DateTime,
    event,
    Date,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from .enums import (
    UserRoleChoice,
    ClientGenderChoice,
)
from ppgc_backend.config.postgres_connection_manager import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,  # auto-generates new UUID on insert
        index=True
    )
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    pin_hash = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    other_names = Column(String)
    gender = Column(
        SQLAlchemyEnum(ClientGenderChoice, name='client_gender_choice')
    )
    account_status = Column(String, default="Active")
    misc = Column(JSON, default=dict, nullable=True)
    user_role = Column(
        SQLAlchemyEnum(UserRoleChoice, name='user_role_choice'),
        nullable=False,
        default=UserRoleChoice.user
    )
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profile_avatar_url = Column(String(1024))

    nin = Column(String)
    date_of_birth = Column(Date, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    email_notification = Column(Boolean, default=True)
    push_notification = Column(Boolean, default=True)
    pass_code = Column(String)

    __table_args__ = (
        CheckConstraint("char_length(nin) = 11", name="check_nin_length_11"),
    )
    __table_args__ = (
        CheckConstraint("char_length(pass_code) = 4", name="check_pass_code_length_4"),
    )


@event.listens_for(User, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()

