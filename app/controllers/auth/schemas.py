from typing import Optional
from pydantic import BaseModel, model_validator, Field


from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from ppgc_backend.app.controllers.actors.schemas import UserResponseSchema # for a purpose

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
    user_role: UserRoleChoice = UserRoleChoice.user


class StaffRegistrationSchema(UserRegistrationSchema):
    user_role: UserRoleChoice = UserRoleChoice.staff


class SignupCodeVerificationSchema(UserRegistrationSchema):
    verification_code: str


class RequestEmailCodeSchema(BaseModel):
    email: str
    first_name: str


class RequestEmailResponseSchema(BaseModel):
    detail: str = Field(..., description = "Success message on sending the code.")
    expiry: str = Field(..., description="Time of expiry in ISO format.")


class VerifyEmailAndSignUserUpSchema(UserRegistrationSchema, PinOrPasswordSchema):
    code: str
    


class GenericSuccessResponseSchema(BaseModel):
    detail: str


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