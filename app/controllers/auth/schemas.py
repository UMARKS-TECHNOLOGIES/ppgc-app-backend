from typing import Optional
from pydantic import BaseModel, model_validator, Field, PrivateAttr

from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from ppgc_backend.app.controllers.actors.schemas import UserResponseSchema # for a purpose

class EmailEtCodeSchema(BaseModel):
    email: str
    code: str

    model_config = {
        "extra": "allow"   # allow arbitrary extra fields
    }

class PinOrPasswordSchema(BaseModel):
    password: Optional[str] = None
    pin: Optional[str] = None

    @model_validator(mode="after")
    def validate_pin_or_password(cls, values):
        check_valid = (
            not(values.password and values.pin) 
            and (
                (values.password and not values.pin) 
                or (values.pin and not values.password)
            )
        )
        if not check_valid:
            raise ValueError("Either of 'pin' or 'password' must be included in the payload. Both can't be empty or non-empty.")
        return values


class UserRegistrationSchema(PinOrPasswordSchema):
    email: str
    first_name: str
    last_name: Optional[str] = None
    other_names: Optional[str] = None
    # user_role: UserRoleChoice = UserRoleChoice.user


class StaffRegistrationSchema(UserRegistrationSchema):
    role_token: str


class SignupCodeVerificationSchema(UserRegistrationSchema):
    verification_code: str


class RequestEmailCodeSchema(BaseModel):
    email: str
    first_name: str
    _reason: EmailManagementReasonChoice = PrivateAttr(default=EmailManagementReasonChoice.email_verification)


class RequestEmailResponseSchema(BaseModel):
    detail: str = Field(..., description = "Success message on sending the code.")
    expiry: str = Field(..., description="Time of expiry in ISO format.")


class VerifyEmailAndSignUserUpSchema(UserRegistrationSchema, EmailEtCodeSchema):
    role_token: Optional[str] = Field(None, description="Optional role-based token for role assignment")


class GenericSuccessResponseSchema(BaseModel):
    detail: str


class StaffLinkGenerateBase(BaseModel):
    role: UserRoleChoice = Field('staff', description="Role to assign (staff, admin, agent)")

class StaffLinkGenerateSchema(BaseModel):
    email: Optional[str] = Field(None, description="Optional target email")
    expires_in_days: int = Field(default=3, ge=1, le=90, description="Token expiry in days (1-90)")


class StaffLinkResponseSchema(BaseModel):
    detail: str
    token: str
    expires_at: str
    role: str


class SigninSchema(PinOrPasswordSchema):
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


class SigninResponse(UserResponseSchema):
    pass

class TokenData(BaseModel):
    email: str | None = None


class PasswordResetSchema(PinOrPasswordSchema):
    email: str
    code: str


class SendPasswordResetMail(BaseModel):
    detail: str
    expiry: str


class Email(BaseModel):
    email: str


class ProbeUserExistenceSchema(BaseModel):
    username: str
    email: str


class SendEmailCodeSchema(ProbeUserExistenceSchema):
    pass


class PasscodeSchema(BaseModel):
    pass_code: str
