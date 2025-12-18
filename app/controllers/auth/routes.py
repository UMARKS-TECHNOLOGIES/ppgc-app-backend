from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, status, Depends, Body, Response, Query


from ppgc_backend.app.database import get_db
from .schemas import (
    Token,
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
    StaffLinkGenerateSchema,
    StaffLinkResponseSchema,
)
from .services import (
    signin,
    create_user,
    handle_refresh,
    revoke_refresh_session,
    decode_user_from_token,
    change_pin_or_password, 
    send_password_reset_mail,
    require_roles,
    confirm_email_verification_code_and_sign_user_up,
    probe_email_uniqueness_and_request_verification_code,
    generate_staff_invite_link,
    validate_role_token,
)
from ppgc_backend.app.controllers.actors.models import User
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice


router = APIRouter(prefix="/auth", tags=["auth"])

# user registeration endpoint
# @router.post("/register-staff/", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def register_user(user_data: StaffRegistrationSchema, db: AsyncSession = Depends(get_db)):
    return await create_user(db, user_data)


# request email verification for signup endpoint
@router.post(
    "/request-email-verification-code/", 
    status_code=status.HTTP_200_OK, 
    response_model = RequestEmailResponseSchema
)
async def check_email_and_request_verification_code_for_signup(
    requester_data: RequestEmailCodeSchema, 
    session: AsyncSession = Depends(get_db)
):
    return await probe_email_uniqueness_and_request_verification_code(session, requester_data)


# confirm email verification endpoint
@router.post(
    "/confirm-email-verification-code/",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def confirm_email_verification_code_and_signup(
    requester_data: VerifyEmailAndSignUserUpSchema, 
    session: AsyncSession = Depends(get_db),
    role: UserRoleChoice = Depends(validate_role_token),
):
    return await confirm_email_verification_code_and_sign_user_up(
        data = requester_data,
        session = session,
        role_to_assign = role
    )


# signin endpoint
@router.post("/signin/", response_model=SigninResponse, status_code=status.HTTP_200_OK)
async def signin_for_access_token(user_data: SigninSchema, request: Request, response: Response, session: AsyncSession = Depends(get_db)):
    return await signin(session, user_data.model_dump(), request, response)


@router.post("/refresh/{id}/", response_model=Token)
async def refresh_token(
    id: int,
    refresh_token: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    return await handle_refresh(db, refresh_token, id)


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


@router.delete("/logout/", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response = Depends(revoke_refresh_session),
):
    """Logout by revoking the refresh token for the authenticated user."""
    return response


@router.post(
    "/generate-staff-invite-token/",
    status_code=status.HTTP_201_CREATED,
    response_model=StaffLinkResponseSchema,
    response_description="Staff invite link generated"
)
async def generate_staff_link(
    data: StaffLinkGenerateSchema,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin"))
):
    """
    Generate a staff invite link (admin-only).
    
    - **role**: Role to assign (staff, admin, agent)
    - **email**: Optional target email
    - **expires_in_days**: Link expiry in days (1-90, default 7)
    """
    result = await generate_staff_invite_link(
        db=db,
        admin_user=admin,
        email=data.email,
        expires_in_days=data.expires_in_days
    )
    
    return StaffLinkResponseSchema(
        detail="Staff invite link generated successfully",
        token=result["token"],
        expires_at=result["expires_at"],
        role=result["role"]
    )