import random
import secrets
import asyncio
from sqlalchemy import and_
from jose import jwt, JWTError
from typing import Optional
from sqlalchemy import delete, or_
from sqlalchemy.future import select
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from typing import Callable, Literal, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, Request, Response, Query

from .schemas import (
    EmailEtCodeSchema,
    PinOrPasswordSchema,
    UserRegistrationSchema,
    RequestEmailCodeSchema,
    ProbeUserExistenceSchema,
    VerifyEmailAndSignUserUpSchema,
)
from .models import RefreshSession, RoleBasedToken
from .utils import is_secure_request
from ppgc_backend.app.initiator import logger
from ppgc_backend.app.models import (
    User,
    TransientVerificationStore
)
from ppgc_backend.config import env_is_test
from ppgc_backend.app.utils.store import (
    send_email,
    substituted_string,
    transient_cleanup_interval,
    email_verification_code_ttl,
    read_email_from_html_template_name,
)
from ppgc_backend.app.database import get_db
from ppgc_backend.config.settings import (
    DEBUG,
    JWT_ALGORITHM,
    ACCESS_SECRET_KEY, 
    PASSWORD_RESET_TTL,
    REFRESH_SECRET_KEY,
    JWT_EXPIRATION_DELTA, 
    SUPER_ADMIN_PASSWORD,
    TEST_PASSWORD_RESET_TTL,
    SUPER_ADMIN_EMAIL_ADDRESS,
    REFRESH_TOKEN_EXPIRY_MINUTES,
)
from ppgc_backend.log_config.logger_config import log_error
from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from ppgc_backend.config.postgres_connection_manager import get_postgres_instance
from ppgc_backend.app.enums import EmailManagementReasonChoice as TransientReason


import logging

logger = logging.getLogger(__name__)

# Constants for JWT
SECRET_KEY = ACCESS_SECRET_KEY
ALGORITHM = JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = JWT_EXPIRATION_DELTA

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
router = APIRouter()

def verify_token(plain_token, hashed_token):
    return pwd_context.verify(plain_token, hashed_token)


def verify_password(plain_password, hashed_password):
    return verify_token(plain_password, hashed_password)


def hash_token(token):
    return pwd_context.hash(token)


def get_password_hash(password):
    return hash_token(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token(data: dict, expiry: datetime, sec_key: str) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": expiry})
    encoded_jwt = jwt.encode(
        to_encode,
        sec_key,
        algorithm=JWT_ALGORITHM,
    )
    return encoded_jwt


def fetch_token(user: User, type: Literal['access, refresh']) -> Tuple[str, datetime]:
    if type not in ["access","refresh"]:
        raise ValueError("Token type should either be 'access' or 'refresh'")
    type_is_access = type == 'access' 
    expiry_minutes = (ACCESS_TOKEN_EXPIRE_MINUTES 
        if type_is_access
        else REFRESH_TOKEN_EXPIRY_MINUTES
    )
    token_expiry = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    sec_key = ACCESS_SECRET_KEY if type_is_access else REFRESH_SECRET_KEY
    return create_token({"sub": user.email}, token_expiry, sec_key), token_expiry


def fetch_access_token(user: User) -> dict:
    access_token,_ = fetch_token(user,'access')
    return {"access_token": access_token, "token_type": "bearer"}


async def handle_refresh(db: AsyncSession, refresh_token: str, refresh_id: int):
    payload = jwt.decode(
        refresh_token,
        REFRESH_SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
        
    user = (await db.execute(select(User).where(
        User.email == email
    ))).scalars().one()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email.")

    # Optionally: verify refresh token exists in DB/Redis here
    refresh_instance = (await db.execute(
        select(RefreshSession)
        .where(
            RefreshSession.user_id == user.id,
            RefreshSession.id == refresh_id
        )
    )).scalars().one()
    
    now = datetime.now(timezone.utc)
    if refresh_instance.expires_at <= now:
        await db.delete(refresh_instance)
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")

    if not verify_token(refresh_token, refresh_instance.token_hash):
        # Token reuse detected — revoke all sessions for this user
        await db.execute(
            delete(RefreshSession).where(
                RefreshSession.user_id == user.id
            )
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Generate a new access token
    return fetch_access_token(user)


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


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_session_id(request: Request):
    session_id_str = request.cookies.get("session_id")
    session_id = int(session_id_str) if session_id_str else None
    if not session_id:
        if DEBUG:
            logger.error("** Session id not found.")
        credentials_exception
    return session_id

# Session token validity
async def decode_user_from_token(
    request: Request,
    session_id: int = Depends(get_session_id),
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db),
):
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
    
    # Retrieve session from cookies
    now = datetime.now(timezone.utc)
    refresh_instance = (await db.execute(
        select(RefreshSession)
        .where(
            RefreshSession.id == session_id,
            RefreshSession.user_id == user.id
        )
    )).scalars().first()
    if (
        (not refresh_instance) 
        or (not verify_token(token, refresh_instance.access_token_hash))
        or (now > refresh_instance.expires_at)
    ):
        raise credentials_exception
    

    user.refresh = { "id": session_id } # Include for session-related acts
    request.state.db = db # inject the db session
    request.state.user = user # inject the user
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
    email_address: str,
    email_code: str,
    reason: TransientReason
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
            async with get_postgres_instance() as session:
                session: AsyncSession
                try:
                    transient_instance = (await session.execute(
                        select(TransientVerificationStore)
                        .where(
                            and_(
                                TransientVerificationStore.email_address == email_address,
                                TransientVerificationStore.email_code == email_code,
                                TransientVerificationStore.reason == reason
                            )
                        )
                    )).scalars().first()

                    if not transient_instance: # When instance has been deleted
                        break

                    now = datetime.now(timezone.utc)
                    expiry = transient_instance.email_code_expiry_time
                    if expiry >= now: # Delete the expiry time
                        await session.delete(transient_instance)
                        await session.commit()
                        # break the loop
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


async def handle_email_code_request(
    reason: TransientReason,
    db: AsyncSession,
    email: str,
    email_name_placeholder: str,
):
    # Check if the request already exists
    query = await db.execute(
        select(TransientVerificationStore)
        .where(
            TransientVerificationStore.email_address == email,
            TransientVerificationStore.reason == reason
        )
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
     
    # Generate and send verification code
    code = await request_verification_code(email, email_name_placeholder)

    try:
        # Get or create transient verification store entry
        verification_instance = (await db.execute(
            select(TransientVerificationStore)
            .where(
                TransientVerificationStore.email_address == email,
                TransientVerificationStore.reason == reason,
            )
        )).scalars().first()

        expiry_time = datetime.now(timezone.utc) + timedelta(seconds=email_verification_code_ttl())

        if not verification_instance:
            verification_instance = TransientVerificationStore(
                email_address=email,
                reason = reason
            )

        verification_instance.email_code = code
        verification_instance.email_code_expiry_time = expiry_time

        db.add(verification_instance)
        await db.commit()

        # Start cleanup task
        await email_code_cleanup_loop(email, code, reason)

        return expiry_time
    except Exception as e:
        await db.rollback()
        f_msg=f"Error processing email code"
        d_msg=f"Error Caching Email code detail: {str(e)}"
        if DEBUG:
            logger.error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


# user existence
async def probe_email_uniqueness_and_request_verification_code(session: AsyncSession, data: RequestEmailCodeSchema):
    email = data.email
    name = data.first_name
    
    # query email uniqueness from the user's database
    email_query = await session.execute(
        select(User)
        .where(User.email == email)
    )
    email_exists = email_query.scalars().first()
    if email_exists:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = f"Email {email} already exists"
        )
    
    expiry_time = await handle_email_code_request(data._reason,session,email,name)
    
    return {
        "detail" : f"A verification code has been sent to the email {email}. Also check your spam folder.",
        "expiry": expiry_time.isoformat()
    }


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


# decorator
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
    role_to_assign: Optional[UserRoleChoice] = None,
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

    # Use role from token if available, otherwise use the role from data
    user_role = role_to_assign if role_to_assign else data.user_role

    try:
        # Add the new user to the session and commit the transaction
        session.add(User(
            first_name = data.first_name,
            email = data.email,
            email_verified=True,
            user_role=user_role,
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
    

async def signin(db:AsyncSession, user_data: dict, request: Request, response: Response):
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
    
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
        
    try:
        access_token, _ = fetch_token(user,'access')
        refresh_token, refresh_expiry = fetch_token(user,'refresh')
        # add the session token
        refresh_inst = RefreshSession(
            user_id = user.id,
            access_token_hash = hash_token(access_token),
            token_hash = hash_token(refresh_token),
            expires_at = refresh_expiry,
            user_agent = user_agent,
            ip_address = ip_address,
        )
        db.add(refresh_inst)
        await db.flush()
        await db.commit()
        user.access_token = access_token
        user.refresh = {
            "id": refresh_inst.id,
            "token": refresh_token
        }

        # set cookie
        response.set_cookie(
            key="session_id",
            value=str(user.refresh["id"]),
            httponly=True,
            secure=is_secure_request(request),          # True in production (HTTPS)
            samesite="lax",        # or "strict"
            max_age= REFRESH_TOKEN_EXPIRY_MINUTES * 60,  # 30 days
            path="/",
        )
        return user
    except Exception as e:
        f_message = 'An error occured while signing user in!'
        d_err_message = f'An error occured while signing user in! Reason:{e}'
        logger.error(d_err_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f_message
        )


async def initialize_admin(session: AsyncSession):
    email = SUPER_ADMIN_EMAIL_ADDRESS
    password = SUPER_ADMIN_PASSWORD
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
            await email_code_cleanup_loop(email, code, reason)

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


async def revoke_refresh_session(    
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(decode_user_from_token),
):
    """Mark a refresh token as revoked for the given user."""
    session = (await db.execute(
        select(RefreshSession)
        .where(
            RefreshSession.id == user.refresh["id"], 
            RefreshSession.user_id == user.id)
    )).scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found")
    await db.delete(session)
    await db.commit()

    # delete the cookie
    response.delete_cookie(
        key="session_id",
        path="/",          # MUST match the original path
        domain=None,       # Must match if you set one
    )


async def generate_staff_invite_link(
    db: AsyncSession,
    admin_user: User,
    email: Optional[str] = None,
    expires_in_days: int = 3,
    role: UserRoleChoice = 'staff',
) -> dict:
    """Generate a unique staff invite link with role-based token.
    
    Args:
        role: Role to assign ('staff', 'admin', 'agent')
        db: AsyncSession
        admin_user: The admin user creating the link
        email: Optional target email for the link
        expires_in_days: Days until link expires (1-90)
    
    Returns:
        dict with token, expiry, and role info
    """
    # Validate role
    valid_roles = [r.value for r in UserRoleChoice]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Generate a time-based unique token (random part + timestamp)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    random_part = secrets.token_urlsafe(24)
    plain_token = f"{random_part}.{timestamp}"

    # Calculate expiry
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    
    try:
        role_token = RoleBasedToken(
            role=role,
            token=plain_token,
            email=email,
            expires_at=expires_at,
            created_by_id=admin_user.id
        )
        
        db.add(role_token)
        await db.commit()
        
        if DEBUG:
            logger.info(f'**Generated staff invite token for role {role}')
        
        return {
            "token": plain_token,
            "expires_at": expires_at.isoformat(),
            "role": role.lower()
        }
    
    except Exception as e:
        await db.rollback()
        msg = f'**Error generating staff invite link. Reason: {e}'
        if DEBUG:
            logger.error(msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating invite link"
        )


async def validate_role_token(
    data: VerifyEmailAndSignUserUpSchema,
    db: AsyncSession = Depends(get_db),
) -> UserRoleChoice | None:
    """Validate a role token and mark it as used.
    
    Args:
        token: Plain text token to validate
        db: AsyncSession
    
    Returns:
        Role name if valid and not expired, None otherwise
    """
    token = data.role_token
    role = None
    if token:
        # Find token by hash matching (we need to check all tokens since we hash)
        result = await db.execute(
            select(RoleBasedToken).where(
                RoleBasedToken.token == token,
                RoleBasedToken.is_used == False,
            )
        )
        matching_token = result.scalars().first()
    
        # Check expiry
        now = datetime.now(timezone.utc)
        if not matching_token or matching_token.expires_at <= now:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail="Role token expired or malformed"
            )
        
        role = matching_token.role
        await db.delete(matching_token)
        await db.commit()
    
    return role