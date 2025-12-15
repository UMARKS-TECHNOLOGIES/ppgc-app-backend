import re
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
from sqlalchemy.orm import validates
from pydantic import ValidationError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .enums import (
    UserRoleChoice,
    ClientGenderChoice,
)
from ppgc_backend.app.schemas import CloudImageCreateSchema
from ppgc_backend.config.postgres_connection_manager import Base
from sqlalchemy.orm import relationship


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

    profile_avatar = Column(JSONB)

    nin = Column(String)
    date_of_birth = Column(Date, nullable=True)
    dial_code = Column(String)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    email_notification = Column(Boolean, default=True)
    push_notification = Column(Boolean, default=True)
    pass_code = Column(String)
    recovery_email = Column(String, nullable=True, unique=True, index=True)
    recovery_email_verified = Column(Boolean, default=False)

    # Relationships
    # session_logs = relationship("SessionLog", back_populates="user")
    # activity_logs = relationship("ActivityLog", back_populates="user")

    # internal variable, not part of database
    _access_token = None  
    _refresh = None  

    __table_args__ = (
        CheckConstraint("char_length(nin) = 11", name="check_nin_length_11"),
        CheckConstraint("char_length(pass_code) = 4", name="check_pass_code_length_4"),
        CheckConstraint("char_length(phone_number) = 10", name="check_phone_no_length_10"),
    )

    @hybrid_property
    def access_token(self):
        """Compute or return the cached token."""
        return self._access_token
    @hybrid_property
    def refresh(self):
        """Compute or return the cached token."""
        return self._refresh

    @access_token.setter
    def access_token(self, token_value):
        """Allow setting the token manually."""
        self._access_token = token_value
    @refresh.setter
    def refresh(self, token_value):
        """Allow setting the token manually."""
        self._refresh = token_value


    @validates("profile_avatar")
    def validate_profile_avatar(self, key, value):
        if value is None:
            return None
        
        # Allow Pydantic model instance
        if isinstance(value, CloudImageCreateSchema):
            return value.model_dump()
        
        # Validate dict input
        try:
            validated = CloudImageCreateSchema(**value)
        except ValidationError as e:
            raise ValueError(f"Invalid profile avatar format: {e}")
        
        return validated.model_dump()
    
    @validates("dial_code")
    def validate_dial_code(self, key, value):
        if value is None:
            return None
        
        # Ensure it starts with '+' and has 1-15 digits
        # pattern = r"^\+\d{1,3}$"
        # if not re.fullmatch(pattern, value):
        #     raise ValueError(f"Invalid dial code format: {value}. Must be like '+123'.")
        if value != '+123':
            raise ValueError(f"Invalid dial code format: {value}. Must be like '+234'.")
        
        return value


@event.listens_for(User, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()

