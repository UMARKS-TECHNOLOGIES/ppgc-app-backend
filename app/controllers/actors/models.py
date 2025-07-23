from sqlalchemy import (
    Column, 
    Integer, 
    String,
    ForeignKey, 
    Boolean, 
    JSON, 
    Enum as SQLAlchemyEnum, 
    func,
    DateTime,
    event,
    Date,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from .enums import (
    UserRoleChoice,
    ClientGenderChoice,
)
from ppgc_backend.config.postgres_connection_manager import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    pin_hash = Column(String, nullable=False)
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

    __table_args__ = (
        CheckConstraint("char_length(nin) = 11", name="check_nin_length_11"),
    )


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
            nullable=True
        )
        user = relationship(
            "User", 
            lazy = "selectin",
            backref="bank_accounts",
            uselist=False
        )


@event.listens_for(User, 'before_insert')
# Listen for the 'before_insert' event to set updated_at
def set_updated_at_before_insert(mapper, connection, target):
    target.updated_at = func.now()

