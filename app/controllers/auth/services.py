import random 
import asyncio
from jose import jwt, JWTError
from typing import List, Callable
from sqlalchemy.future import select
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends


from .schemas import TokenData  # if using a TokenData schema
from ppgc_backend.app.models import (
    User,
    TransientVerificationStore
)
from .schemas import UserRegistrationSchema
from ppgc_backend.app.schemas.auth_schemas import (
    TokenData, 
    ProbeUserExistenceSchema,
)
from ppgc_backend.app.utils.store import (
    send_email,
    substituted_string,
    transient_email_interval,
    email_verification_code_ttl,
    transient_email_verification_ttl,
    read_email_from_html_template_name,
)
from ppgc_backend.config import get_env
from ppgc_backend.app.database import get_db
from ppgc_backend.config.settings import DEBUG
from ppgc_backend.config.settings import JWT_SECRET_KEY, JWT_EXPIRATION_DELTA, JWT_ALGORITHM


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
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# signin
async def authenticate_user(db: AsyncSession, login: str, password: str):
    # Check if the login is either a username or an email
    user_query = select(User).filter((User.username == login) | (User.email == login))
    
    # Execute the query
    result = await db.execute(user_query)
    user = result.scalars().first()

    if not user:
        return False

    # Verify the provided password against the stored password hash
    password_verified =  verify_password(password, user.password_hash)
    pin_verified =  verify_password(password, user.pin_hash)
    if not (password_verified or pin_verified):    
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


def require_roles(*allowed_roles: List[str]) -> Callable:
    async def wrapper(current_user: TokenData = Depends(decode_user_from_token)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user  # Optionally return for access
    return wrapper


# Signup
async def create_user(
    db: AsyncSession, 
    user_data: UserRegistrationSchema
):
    username = user_data.username or user_data.email.strip().split('@')[0]
    existing_user = await db.execute(
        select(User).filter((User.email == user_data.email) | (User.username == username))
    )
    existing_user = existing_user.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or Username already exists")

    hashed_password = get_password_hash(user_data.password)
    # clone the model so deleting the password entry wont affect the original schema
    cloned_data = user_data.model_copy()
    # convert the user_data to a dictionary
    user_map = vars(cloned_data)
    # remove the password field
    user_map.pop('password')

    # instantiate a user object
    user = User(
        password_hash=hashed_password,
        **user_map,
    )
    
    try:
        db.add(user)
        # Writes changes to the database but does not commit them.
        # Ensure the user is added and has an ID
        await db.flush()  
        # Commit the transaction to make changes permanent
        await db.commit()  
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    
    # Ensure the user instance reflects the latest state from the database
    await db.refresh(user)
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
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).filter(User.username == token_data.username))
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
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None

    # Query the user in the database
    result = await db.execute(select(User).filter(User.username == username))
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
                if DEBUG:
                    print("❗ Error in email_code_cleanup_loop:", str(e))

            # time in seconds before the next check
            await asyncio.sleep(transient_email_interval())
    
    task = asyncio.create_task(run_cache_task())
    
    #if get_env() == 'test':
    #    await task  # ensure cleanup before test exits

# user existence
async def probe_email_uniqueness_and_request_verification_code(session: AsyncSession, data: dict):
    email_address = data['email']
    fullname = data['fullname']
    
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

    code = await request_verification_code(email_address, fullname)

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
        f_message = "An error occured while registering user."
        d_message= f"{f_message} Reason: {e}" 
        logger.error(d_message)
        raise Exception(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f_message
        )


async def request_verification_code(email_address:str, username: str) -> str:
    
    code = '{:04d}'.format(random.randint(0, 9999))
    
    try:
        await send_email_verification_code(
            code = code,
            user_name = username,
            email_address=email_address
        )
    except Exception as e:
        f_message = "An error occured while sending verification email"
        d_message= f"{f_message} Reason: {e}" 
        logger.error(d_message)
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f_message
        )
    
    return code


async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return user


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
        

async def confirm_email_verification_code_and_sign_user_up(
    data: dict, 
    session: AsyncSession,
):
    # Fetch the record
    stmt = select(TransientVerificationStore).where(
        TransientVerificationStore.email_address == data['email'],
        TransientVerificationStore.email_code == data['code'],
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification code incorrect or expired."
        )

    collection = {}

    # Hash the user's password or pin before saving it to the database
    if 'pin' in data:
        collection['pin_hash'] = get_password_hash(data['pin'])
    elif 'password' in data:
        collection['password_hash'] = get_password_hash(data['password'])

    # extracting names from the fullname
    name_list = data['fullname'].split()
    
    # adding the first_name
    first_name = name_list[0]
    collection['first_name'] = first_name
    # adding last_name
    if len(name_list) > 1:
        last_name = name_list[-1]
        collection['last_name'] = last_name
    # Adding other_names (middle names or any names between the first and last)
    if len(name_list) > 2:
        other_names = " ".join(name_list[1:-1])
        collection['other_names'] = other_names
    


    try:
        # Add the new user to the session and commit the transaction
        session.add(User(
            email = data['email'],
            **collection
        ))

        # delete the verification code from Redis after successful registration
        await session.delete(record)

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
        db = db, 
        login = user_data['email'], 
        password = user_data['password'] if 'password' in user_data else user_data['pin']
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        **fetch_access_token(user),
    }