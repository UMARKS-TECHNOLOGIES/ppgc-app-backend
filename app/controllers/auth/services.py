import random 
import asyncio
from typing import Callable
from jose import jwt, JWTError
from sqlalchemy import delete, or_
from sqlalchemy.future import select
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends

from .schemas import (
    EmailEtCodeSchema,
    PinOrPasswordSchema,
    VerifyEmailAndSignUserUpSchema,
)
from ppgc_backend.app.initiator import logger
from ppgc_backend.app.models import (
    User,
    TransientVerificationStore
)
from ppgc_backend.app.controllers.auth.schemas import (
    UserRegistrationSchema,
    ProbeUserExistenceSchema,
)
from ppgc_backend.config import env_is_test
from ppgc_backend.app.utils.store import (
    send_email,
    substituted_string,
    transient_cleanup_interval,
    email_verification_code_ttl,
    transient_email_verification_ttl,
    read_email_from_html_template_name,
)
from ppgc_backend.app.database import get_db
from ppgc_backend.config import get_env
from ppgc_backend.config.settings import (
    DEBUG,
    JWT_ALGORITHM,
    JWT_SECRET_KEY, 
    PASSWORD_RESET_TTL,
    JWT_EXPIRATION_DELTA, 
    SUPER_ADMIN_PASSWORD,
    TEST_PASSWORD_RESET_TTL,
    SUPER_ADMIN_EMAIL_ADDRESS,
)
from ppgc_backend.log_config.logger_config import log_error
from ppgc_backend.app.enums import EmailManagementReasonChoice


import logging

logger = logging.getLogger(__name__)

# Constants for JWT
SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = JWT_EXPIRATION_DELTA

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
router = APIRouter()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def fetch_access_token(user: User):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# signin
async def authenticate_user(db: AsyncSession, login: str, **kwargs):
    # Check if the login is either a username or an email
    user_query = select(User).filter((User.username == login) | (User.email == login))
    
    # Execute the query
    result = await db.execute(user_query)
    user = result.scalars().first()

    if not user:
        return False
    
    password = kwargs.get('password')
    pin = kwargs.get('pin')

    # Verify the provided password against the stored password/pin hash
    verified =  (verify_password(password, user.password_hash)
        if (user.password_hash and password)
        else verify_password(pin, user.pin_hash)
    )
    
    if not verified:  
        return False

    return user


# user existence
async def check_username_email_availability(db: AsyncSession, user_data: ProbeUserExistenceSchema) -> dict:
    username = user_data.username
    email = user_data.email

    result = {
        "username": "available",
        "email": "available"
    }
    
    # Check if the username exists
    user_by_username = await db.execute(select(User).filter(User.username == username))
    user_by_username = user_by_username.scalars().first()
    
    if user_by_username:
        result["username"] = "unavailable"
    
    # Check if the email exists
    user_by_email = await db.execute(select(User).filter(User.email == email))
    user_by_email = user_by_email.scalars().first()
    
    if user_by_email:
        result["email"] = "unavailable"
    
    return result


def require_roles(*allowed_roles: tuple[str]) -> Callable:
    async def wrapper(current_user: User = Depends(decode_user_from_token)):
        if current_user.user_role not in allowed_roles:
            detail="You do not have permission to perform this action"
            if DEBUG:
                log_error(detail)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail
            )
        return current_user  # Optionally return for access
    return wrapper


# Signup
async def create_user(
    db: AsyncSession, 
    user_data: UserRegistrationSchema
):
    existing_user = await db.execute(
        select(User).filter(User.email == user_data.email)
    )
    existing_user = existing_user.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or Username already exists")

    user_data_to_dict = user_data.model_dump(exclude={"password", "pin"})
    if user_data.pin:
        user_data_to_dict['pin_hash'] = get_password_hash(user_data.pin)
    elif user_data.password:
        user_data_to_dict['password_hash'] = get_password_hash(user_data.password)

    # instantiate a user object
    user = User(
        **user_data_to_dict,
    )
    
    try:
        db.add(user)
        await db.commit()  
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    
    return user


# Session token validity
async def decode_user_from_token(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


async def decode_user_from_token_optional(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Decode user from token without raising exceptions.
    Returns None if the token is invalid or the user is not found.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None

    # Query the user in the database
    result = await db.execute(select(User).filter(User.username == email))
    user = result.scalars().first()
    return user


async def email_code_cleanup_loop(
    session: AsyncSession, 
    email_address: str,
    email_code: str,
):
    """
    Starts a background task to monitor and delete an email verification code
    after it exceeds the email_code_expiry_time.

    Parameters:
        session: AsyncSession - SQLAlchemy async session.
        email_code: str - The verification code to track.
        check_interval_in_secs: int - Frequency of check in seconds.
    """
    async def run_cache_task():
        while True:
            try:
                result = await session.execute(
                    select(TransientVerificationStore)
                    .where(
                        TransientVerificationStore.email_address == email_address,
                        TransientVerificationStore.email_code == email_code,
                    )
                )
                transient_instance = result.scalars().first()

                if not transient_instance:
                    break

                now = datetime.now(timezone.utc)
                expiry = transient_instance.email_code_expiry_time
                if now >= expiry: # Delete the expiry time
                    transient_instance.email_code_expiry_time = None
                    session.add(transient_instance)
                    await session.commit()
                    
                    # sleep the function for transient ttl seconds
                    await asyncio.sleep(transient_email_verification_ttl())

                    # delete the instance if the email_code_expiry_time is None
                    await session.refresh(transient_instance)
                    if not transient_instance.email_code_expiry_time:
                        await session.delete(transient_instance)
                        await session.commit()

                    break

            except Exception as e:
                await session.rollback()
                logger.error("❗ Error in email_code_cleanup_loop:", str(e))

            # time in seconds before the next check
            await asyncio.sleep(transient_cleanup_interval())
    
    task = asyncio.create_task(run_cache_task())
    
    #if get_env() == 'test':
    #    await task  # ensure cleanup before test exits


async def request_verification_code(email_address:str, username: str) -> str:
    
    code = '{:04d}'.format(random.randint(0, 9999))
    
    try:
        await send_email_verification_code(
            code = code,
            user_name = username,
            email_address=email_address
        )
    except Exception as e:
        f_message = "An error occured while requesting verification email"
        d_message= f"{f_message} Reason: {e}" 
        logger.error(d_message)
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f_message
        )
    
    return code


# user existence
async def probe_email_uniqueness_and_request_verification_code(session: AsyncSession, data: dict):
    email_address = data['email']
    first_name = data['first_name']
    
    # query email uniqueness from the user's database
    email_query = await session.execute(
        select(User)
        .where(User.email == email_address)
    )
    email_exists = email_query.scalars().first()
    if email_exists:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = f"Email {email_address} already exists"
        )

    # Check if the request already exists
    query = await session.execute(
        select(TransientVerificationStore)
        .where(TransientVerificationStore.email_address == email_address)
    )
    request_instance = query.scalars().first()
    # raise an exception if an instance and it expiry time exists.
    if request_instance and request_instance.email_code_expiry_time:
        raise HTTPException(
            status_code = status.HTTP_302_FOUND,
            detail = {
                'status' : "An email code has already been sent.",
                'expiry': request_instance.email_code_expiry_time.isoformat()
            }
        )

    code = await request_verification_code(email_address, first_name)

    try:
        # persist code and expiry
        expiry_time = datetime.now(timezone.utc) + timedelta(seconds=email_verification_code_ttl())

        if not request_instance:
            request_instance = TransientVerificationStore(
                email_address = email_address,
            )
        request_instance.email_code = code
        request_instance.email_code_expiry_time = expiry_time
        session.add(request_instance)
        await session.commit()

        # run cleanup task
        await email_code_cleanup_loop(session, email_address, code)

        return {
            "detail" : f"A verification code has been sent to the email {email_address}. Also check your spam folder.",
            "expiry": expiry_time.isoformat()
        }
    except Exception as e:
        await session.rollback()
        f_message = "An error occured after requesting verification email."
        d_message= f"{f_message} Reason: {e}" 
        logger.error(d_message)
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f_message
        )


async def send_email_verification_code(
    code: str,
    user_name: str,
    email_address: str, 
):
    # call the email function and send the email
    # extract the email content from the template
    email_template_content = read_email_from_html_template_name('email_verification_code_template')
    property_street_address = "Port Harcourt"
    
    email_string = substituted_string(
        email_template_content,
        {
            "user_name":user_name,
            "verification_code":code,
            "prince_paradise_address": property_street_address
        }
    )
    from_address="team@stackfinancialsolutions.com"
    subject="PPGC Verification Code"
    from_name="Prince Paradise"
    #to_name="Customer"

    send_email(
        from_email=from_address,
        to_email=email_address,
        from_name=from_name,
        subject=subject,
        html_email=email_string
    )


async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return user


def confirm_email_verification_code(func):
    async def wrapper( data: EmailEtCodeSchema, session: AsyncSession, *args, **kwargs):
        record = (await session.execute(select(TransientVerificationStore).where(
            TransientVerificationStore.email_address == data.email,
            TransientVerificationStore.email_code == data.code,
        ))).scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification code incorrect or expired."
            )
        await session.delete(record)
        await session.commit()
        
        #==========================
        # run actual functionality
        #==========================
        return await func(data, session, *args, **kwargs)
    return wrapper


@confirm_email_verification_code
async def confirm_email_verification_code_and_sign_user_up(
    data: VerifyEmailAndSignUserUpSchema, 
    session: AsyncSession,
):
    collection = {}

    # Hash the user's password or pin before saving it to the database
    if data.pin:
        collection['pin_hash'] = get_password_hash(data.pin)
    elif data.password:
        collection['password_hash'] = get_password_hash(data.password)

    # adding last_name
    last_name = data.last_name
    if last_name:
        collection['last_name'] = last_name
    # Adding other_names
    other_names = data.other_names
    if other_names:
        collection['other_names'] = other_names

    try:
        # Add the new user to the session and commit the transaction
        session.add(User(
            first_name = data.first_name,
            email = data.email,
            email_verified=True,
            user_role=data.user_role,
            **collection
        ))

        await session.commit()

        return {
            "detail": "Email verified and user registered.",
        }

    except Exception as e:
        f_message = "An error occured while creating the user"
        d_message= f"{f_message} Reason: {e}" 
        logger.error(d_message)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user."
        )
    

async def signin(db:AsyncSession, user_data: dict):
    user = await authenticate_user(
        db,
        login = user_data.pop('email'), 
        **user_data
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        token_data = fetch_access_token(user)
        user.access_token = token_data['access_token']
        return user
    except Exception as e:
        f_message = 'An error occured while signing user in!'
        d_err_message = f'An error occured while signing user in! Reason:{e}'
        logger.error(d_err_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f_message
        )


async def initialize_admin():
    email = SUPER_ADMIN_EMAIL_ADDRESS
    password = SUPER_ADMIN_PASSWORD
    async for session in get_db():
        session: AsyncSession
        query = await session.execute(
            select(User)
            .where(
                User.email == email,
                User.user_role == 'admin',
                User.is_admin == True,
            )
        )
        admin = query.scalars().first()

        admin_recent = True
        if admin:  
            # verify password
            user = await authenticate_user(session, email, password=password)
            if not user:
                admin_recent = False
            else:
                logger.info(f"\033[92m**Admin exists\033[0m")
                return  # admin is valid, done
        
        password_hash = get_password_hash(password)

        if not admin:
            # delete all other admin
            stmt = (
                delete(User)
                .where(
                    or_(
                        User.user_role == "admin",
                        User.email == email,
                        User.is_admin == True
                    )
                )
            )
            await session.execute(stmt)
            await session.commit()

            # create new admin
            admin = User(
                email=email,
                password_hash=password_hash,
                is_admin=True,
                user_role='admin'
            )
        elif not admin_recent:
            admin.password_hash = password_hash
        
        session.add(admin)
        await session.commit()

        logger.info("\033[92m**Admin setup\033[0m")  # green log
        return admin


def get_password_reset_ttl():
    return TEST_PASSWORD_RESET_TTL if env_is_test() else PASSWORD_RESET_TTL


async def send_password_reset_mail(
    email: str, 
    session: AsyncSession,
    ttl_in_secs: int = get_password_reset_ttl(),
):
    """
        `email:reason` is the hset's key 
        the reason is the field
        the code is the value
    """
    query = await session.execute(
        select(User)
        .where(User.email == email)
    )
    user = query.scalars().one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!"
        )

    reason = EmailManagementReasonChoice.password_change.value

    # Check if the code exists in the cache
    query = await session.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == email,
            TransientVerificationStore.reason == reason
        )
    )
    reset_instance = query.scalars().first()

    if reset_instance: #When a result is found
        expiry: datetime = reset_instance.email_code_expiry_time
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail = {
                "message" : "Please wait before requesting a new password link.",
                "expiry" : expiry.isoformat() if expiry else None
            }
        )
    else: # When no result is found
        # Generate a new five-digit code
        code = '{:05d}'.format(random.randint(0, 9999))

        # call the email function and send the email
        # extract the email content from the template
        email_template_content = read_email_from_html_template_name('password_reset_template')
        prince_paradise_address = "Port Harcourt"
        
        email_string = substituted_string(
            email_template_content,
            {
                "reset_code":code,
                "prince_paradise_address": prince_paradise_address
            }
        )
        from_address="team@stackfinancialsolutions.com"
        subject="PPGC Verification Code"
        from_name="Prince Paradise"
        #to_name="Customer"

        send_email(
            from_email=from_address,
            to_email=email,
            from_name=from_name,
            subject=subject,
            html_email=email_string
        )


        try:
            # create an instance of the user with the data
            transient_instance = TransientVerificationStore(
                email_address = email,
                reason = reason,
                email_code=code
            )
            session.add(transient_instance)
            await session.flush()

            expiry_time: datetime = transient_instance.created_at + timedelta(seconds=ttl_in_secs)
            transient_instance.email_code_expiry_time = expiry_time
            await session.commit()

            # run cleanup task
            await email_code_cleanup_loop(session, email, code)

            return {
                "detail":"Password reset email sent!",
                "expiry": expiry_time.isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong sending a password reset mail. Please try again later.",
                headers={"X-Error": "Server error"},
            )
        

async def change_pin_or_password(
    session: AsyncSession,
    **kwargs,
):
    password = kwargs.get('password',None)
    pin = kwargs.get('pin',None)
    code = kwargs.get('code')
    email = kwargs.get('email')

    query = await session.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == email,
            TransientVerificationStore.email_code == code,
        )
    )
    transient_instance = query.scalars().first()

    now = datetime.now(timezone.utc)

    if not transient_instance or transient_instance.email_code_expiry_time < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Password/Pin Request either expired or not initiated!'
        )

    # check that password ain't same
    result = await authenticate_user(session, email, {'password':password,'pin':pin})
    if result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New Password/Pin can't be same as old."
        )
    else:
        query = await session.execute(
            select(User)
            .where(User.email == email)
        )
        user = query.scalars().first()
        if not user:
            if DEBUG:
                logger.info(f'**User not found')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject for Password/Pin change not found!"
            )
        
        if password:
            hash = get_password_hash(password)
            user.password_hash = hash
        elif pin:
            hash = get_password_hash(pin)
            user.pin_hash = hash
        session.add(user)
        await session.commit()

        # delete the transient instance
        await session.delete(transient_instance)
        await session.commit()


def verify_pin_or_password(user: User, data: PinOrPasswordSchema):
    password_verified =  (
        verify_password(data.password, user.password_hash) 
        if user.password_hash and data.password else None
    )
    pin_verified =  (
        verify_password(data.pin, user.pin_hash) 
        if user.pin_hash and data.pin else None
    )
    return (password_verified or pin_verified)