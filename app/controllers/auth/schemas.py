from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator, Field

class TokenData(BaseModel):
    username: str | None = None


class UserSigninSchema(BaseModel):
    username: Optional[str] = None
    email: str = None
    password: str


class RegistrationSchema(BaseModel):
    fullname: str
    email: str


class RequestEmailCodeSchema(RegistrationSchema):
    pass

class RequestEmailResponseSchema(BaseModel):
    detail: str = Field(..., description = "Success message on sending the code.")
    expiry: str = Field(..., description="Time of expiry in ISO format.")


class VerifyEmailAndSignUserUpSchema(RegistrationSchema):
    code: str
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


class UserRegistrationSchema(BaseModel):
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    #last_name: str
    # Add other fields as needed

class GenericSuccessResponseSchema(BaseModel):
    detail: str

class SignupCodeVerificationSchema(UserRegistrationSchema):
    verification_code: str
    fullname: str
    client_type: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SigninResponse(Token):
    user_id: int

class TokenData(BaseModel):
    username: str | None = None

class UserResponseSchema(BaseModel):
    id: int
    email: str
    username: str

    model_config = ConfigDict(from_attributes=True)
