from sqlalchemy import (
    Column, 
    Integer, 
    String,
    Boolean, 
    Enum as SQLAlchemyEnum, 
    func,
    ForeignKey,
    DateTime,
)
from sqlalchemy.future import select
from sqlalchemy import types as _types
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession


from ppgc_backend.app.enums import (
    EmailManagementReasonChoice,
)
from .model_helper import CloudImageDetail
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.config.postgres_connection_manager import Base
from ppgc_backend.app.controllers.bookings.models import Booking
from ppgc_backend.app.controllers.hotels.models import Hotel, Room
from ppgc_backend.app.controllers.properties.models import Property
from ppgc_backend.app.controllers.auth.models import RefreshSession
from ppgc_backend.app.controllers.savings.models import DailySavings
from ppgc_backend.app.controllers.inspection.models import Inspection
from ppgc_backend.app.controllers.investments.models import Investment
from ppgc_backend.app.controllers.transactions.models import Transaction
from ppgc_backend.app.controllers.activity_logging.models import ActivityLog
from ppgc_backend.app.controllers.two_factor_auth.models import TwoFactorAuth
from ppgc_backend.app.controllers.two_factor_auth.models import TwoFactorAuthLog

# cascade="all, delete-orphan"
# this specifies the operations that should "cascade" 
# from the parent object to the related child objects 
# (usually in a one-to-many or many-to-one relationship).

class TransientVerificationStore(Base):
    __tablename__ = 'transient_verification_store'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    email_address = Column(String, nullable=True, unique=True)
    email_code = Column(String(255), nullable=True)
    email_code_expiry_time = Column(DateTime(timezone=True), nullable=True)
    email_address_verified = Column(Boolean, default=False)
    
    email_link = Column(String, nullable=True)
    email_link_time = Column(
        _types.TIMESTAMP(timezone=True),
        server_default=func.now(),  # Sets the default value on insert
        onupdate=func.now(),        # Updates the value on update
        nullable=True
    )
    reason = Column(SQLAlchemyEnum(EmailManagementReasonChoice, name='email_management_reason_choice'), nullable=True)

    def __str__(self):
        return f"{self.email_address} - {self.reason.value}"

    @classmethod
    async def email_exists(cls, db_session: AsyncSession, email: str) -> bool:
        """
        Check if an instance with the given email address exists.

        Args:
        - db_session (AsyncSession): SQLAlchemy async session to use for the query.
        - email (str): The email address to check.

        Returns:
        - bool: True if an instance with the given email address exists, else False.
        """
        result = await db_session.execute(
            select(cls).filter(cls.email_address == email)
        )
        return result.scalars().first() is not None
    
    @classmethod
    async def check_email_code_exists(cls, db_session: AsyncSession, email_code_to_check: str) -> bool:
        """
        Check if a code exists in this model.

        Args:
        - db_session (AsyncSession): SQLAlchemy async session to use for the query.
        - email_code_to_check (str): The email code to check.

        Returns:
        - bool: True if an instance with the given email code exists, else False.
        """
        result = await db_session.execute(
            select(cls).filter(cls.email_code == email_code_to_check)
        )
        return result.scalars().first() is not None



class Area(Base):
    __tablename__ = 'areas'

    id = Column(Integer, primary_key=True, index=True)
    
    # For international usage, consider using a library like pycountry or geopy for validating country/state/city combinations.
    country = Column(String, nullable=False) # e.g., Nigeria
    state_or_province = Column(String, nullable=False) # e.g., "California" or "Lagos"
    city_or_town = Column(String, nullable=False) # e.g., "San Francisco" or "Ikeja"
    county = Column(String) # US-based e.g., "Los Angeles County"
    street = Column(String) # e.g., "Market Street", "Ahmadu Bello Way"
    building_name_or_suite = Column(String) # e.g., "Apt 402"
    zip_or_postal_code = Column(String) # e.g., 500102



models = [
    User,
    Room,
    Hotel,
    Booking,
    Property,
    Investment, 
    Inspection,
    ActivityLog,
    Transaction,
    DailySavings,
    TwoFactorAuth,
    RefreshSession,
    TwoFactorAuthLog,
]