from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, status, Depends


from ppgc_backend.app.database import get_db
from ppgc_backend.app.schemas.auth_schemas import (
    SigninResponse, 
)
from .schemas import (
    RequestEmailCodeSchema,
    UserRegistrationSchema,
    RequestEmailResponseSchema,
    GenericSuccessResponseSchema,
    VerifyEmailAndSignUserUpSchema,
    SigninSchema,
)
from .services import (
    signin,
    create_user, 
    fetch_access_token, 
    confirm_email_verification_code_and_sign_user_up,
    probe_email_uniqueness_and_request_verification_code
)


router = APIRouter(prefix="/auth", tags=["auth"])

# user registeration endpoint
# @router.post("/register", status_code=status.HTTP_201_CREATED)
# async def register_user(user_data: UserRegistrationSchema, db: AsyncSession = Depends(get_db)):
#     try:
#         user = await create_user(db, user_data)
#     except HTTPException as e:
#         raise e
#     return fetch_access_token(user)


# request email verification for signup endpoint
@router.post(
    "/request-email-verification-code", 
    status_code=status.HTTP_200_OK, 
    response_model = RequestEmailResponseSchema
)
async def check_email_and_request_verification_code(
    requester_data: RequestEmailCodeSchema, 
    session: AsyncSession = Depends(get_db)
):
    return await probe_email_uniqueness_and_request_verification_code(session, requester_data.model_dump())


# confirm email verification endpoint
@router.post(
    "/confirm-email-verification-code",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def confirm_email_verification_code_and_signup(
    requester_data: VerifyEmailAndSignUserUpSchema, 
    session: AsyncSession = Depends(get_db),
):
    return await confirm_email_verification_code_and_sign_user_up(
        data = requester_data.model_dump(),
        session = session
    )


# signin endpoint
@router.post("/signin", response_model=SigninResponse, status_code=status.HTTP_200_OK)
async def signin_for_access_token(user_data: SigninSchema, session: AsyncSession = Depends(get_db)):
    return await signin(session, user_data.model_dump())
