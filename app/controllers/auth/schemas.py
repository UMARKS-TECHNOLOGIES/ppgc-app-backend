from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator, Field


from ppgc_backend.app.controllers.actors.enums import UserRoleChoice

class RegistrationSchema(BaseModel):
    fullname: str
    email: str


class RequestEmailCodeSchema(RegistrationSchema):
    pass


class RequestEmailResponseSchema(BaseModel):
    detail: str = Field(..., description = "Success message on sending the code.")
    expiry: str = Field(..., description="Time of expiry in ISO format.")


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
    

class VerifyEmailAndSignUserUpSchema(RegistrationSchema, PinOrPasswordSchema):
    code: str


class GenericSuccessResponseSchema(BaseModel):
    detail: str


class SigninSchema(PinOrPasswordSchema):
    email: str


class UserRegistrationSchema(PinOrPasswordSchema):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class StaffRegistrationSchema(UserRegistrationSchema):
    user_role: str = 'staff'


class Token(BaseModel):
    access_token: str
    token_type: str


class SigninResponse(Token):
    pass

class TokenData(BaseModel):
    email: str | None = None

class UserResponseSchema(BaseModel):
    id: int
    email: str
    email_verified: bool
    user_role: UserRoleChoice

    model_config = ConfigDict(from_attributes=True)

class PasswordResetSchema(PinOrPasswordSchema):
    email: str
    code: str

class SendPasswordResetMail(BaseModel):
    detail: str
    expiry: str

class Email(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str


class SigninResponse(Token):
    pass


class UserSigninSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class ProbeUserExistenceSchema(BaseModel):
    username: str
    email: str

class SendEmailCodeSchema(ProbeUserExistenceSchema):
    pass

class RequestEmailCodeSchema(BaseModel):
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    #last_name: str
    # Add other fields as needed


class SignupCodeVerificationSchema():
    verification_code: str
    fullname: str
    client_type: str
