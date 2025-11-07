from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, status, Depends, Body


from ppgc_backend.app.database import get_db
from .schemas import (
    Email,
    SigninSchema,
    PasscodeSchema,
    SigninResponse,
    UserResponseSchema,
    PasswordResetSchema,
    SendPasswordResetMail,
    RequestEmailCodeSchema,
    StaffRegistrationSchema,
    RequestEmailResponseSchema,
    GenericSuccessResponseSchema,
    VerifyEmailAndSignUserUpSchema,
)
from .services import (
    signin,
    create_user,
    decode_user_from_token,
    change_pin_or_password, 
    send_password_reset_mail,
    confirm_email_verification_code_and_sign_user_up,
    probe_email_uniqueness_and_request_verification_code,
)
from ppgc_backend.app.controllers.actors.models import User


router = APIRouter(prefix="/auth", tags=["auth"])

# user registeration endpoint
@router.post("/register-staff/", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def register_user(user_data: StaffRegistrationSchema, db: AsyncSession = Depends(get_db)):
    return await create_user(db, user_data)


# request email verification for signup endpoint
@router.post(
    "/request-email-verification-code/", 
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
    "/confirm-email-verification-code/",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def confirm_email_verification_code_and_signup(
    requester_data: VerifyEmailAndSignUserUpSchema, 
    session: AsyncSession = Depends(get_db),
):
    return await confirm_email_verification_code_and_sign_user_up(
        data = requester_data.model_dump(exclude_none=True),
        session = session
    )


# signin endpoint
@router.post("/signin/", response_model=SigninResponse, status_code=status.HTTP_200_OK)
async def signin_for_access_token(user_data: SigninSchema, session: AsyncSession = Depends(get_db)):
    return await signin(session, user_data.model_dump())


@router.post("/send-password-reset-mail/", response_model=SendPasswordResetMail)
async def send_password_reset_mail_endpoint(
    data: Email = Body(...),
    session: AsyncSession = Depends(get_db),
):
    return await send_password_reset_mail(data.email, session)


@router.post("/change-pin-or-password/")
async def change_password_endpoint(
    data: PasswordResetSchema = Body(...),
    session: AsyncSession = Depends(get_db),
):
    return await change_pin_or_password(
        session=session,
        **data.model_dump()
    )


@router.post("/confirm-passcode/")
async def confirm_passcode_endpoint(
    data: PasscodeSchema = Body(...),
    user: User = Depends(decode_user_from_token)
):
    return user.pass_code == data.pass_code