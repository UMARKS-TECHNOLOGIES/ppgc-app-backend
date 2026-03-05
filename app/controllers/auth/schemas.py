from typing import Optional
from pydantic import BaseModel, model_validator, Field, PrivateAttr

from ppgc_backend.app.enums import EmailManagementReasonChoice
from ppgc_backend.app.controllers.actors.enums import UserRoleChoice
from ppgc_backend.app.controllers.actors.schemas import UserResponseSchema # for a purpose


class Email(BaseModel):
    email: str

class EmailEtCodeSchema(BaseModel):
    """Payload containing an email address and a verification code."""

    email: str = Field(..., description="User email address")
    code: str = Field(..., description="Verification code sent to the email")

    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "description": "Schema for submitting an email and its associated verification code."
        }
    }


class PinOrPasswordSchema(BaseModel):
    """Base schema that enforces either a PIN or a password, but not both."""

    password: Optional[str] = Field(
        None, description="User password (mutually exclusive with PIN)"
    )
    pin: Optional[str] = Field(
        None, description="4-digit PIN (mutually exclusive with password)"
    )

    @model_validator(mode="after")
    def validate_pin_or_password(cls, values):
        check_valid = (
            not (values.password and values.pin)
            and (
                (values.password and not values.pin)
                or (values.pin and not values.password)
            )
        )
        if not check_valid:
            raise ValueError(
                "Either of 'pin' or 'password' must be included. Both cannot be empty or provided together."
            )
        return values

    model_config = {
        "json_schema_extra": {
            "description": "Schema enforcing authentication using either a password or a PIN."
        }
    }


class UserRegistrationSchema(PinOrPasswordSchema):
    """Base schema for registering a new user."""

    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    other_names: Optional[str] = Field(None, description="Other user names")

    model_config = {
        "json_schema_extra": {
            "description": "Schema used for registering a standard user."
        }
    }


class StaffRegistrationSchema(UserRegistrationSchema):
    """Schema for registering staff users using a role token."""

    role_token: str = Field(..., description="Role-based token for staff registration")

    model_config = {
        "json_schema_extra": {
            "description": "Schema for staff registration using a role token."
        }
    }


class SignupCodeVerificationSchema(UserRegistrationSchema):
    """Schema for verifying email code during signup."""

    verification_code: str = Field(
        ..., description="Email verification code sent during signup"
    )

    model_config = {
        "json_schema_extra": {
            "description": "Schema for verifying a signup email code."
        }
    }


class RequestEmailCodeSchema(BaseModel):
    """Schema for requesting an email verification code."""

    email: str = Field(..., description="Target email address")
    first_name: str = Field(..., description="First name of the user")

    _reason: EmailManagementReasonChoice = PrivateAttr(
        default=EmailManagementReasonChoice.email_verification
    )

    model_config = {
        "json_schema_extra": {
            "description": "Schema for requesting an email verification code."
        }
    }


class RequestEmailResponseSchema(BaseModel):
    """Response returned after requesting an email code."""

    detail: str = Field(..., description="Success message")
    expiry: str = Field(..., description="Expiry time of the code in ISO format")

    model_config = {
        "json_schema_extra": {
            "description": "Response returned after sending an email verification code."
        }
    }


class VerifyEmailAndSignUserUpSchema(UserRegistrationSchema, EmailEtCodeSchema):
    """Schema for verifying email and completing user registration."""

    role_token: Optional[str] = Field(
        None, description="Optional role-based token for role assignment"
    )

    model_config = {
        "json_schema_extra": {
            "description": "Schema for verifying email and signing up a user."
        }
    }


class GenericSuccessResponseSchema(BaseModel):
    """Generic success response."""

    detail: str = Field(..., description="Success message")

    model_config = {
        "json_schema_extra": {
            "description": "Generic success response schema."
        }
    }


class StaffLinkGenerateBase(BaseModel):
    """Base schema for generating staff invite links."""

    role: UserRoleChoice = Field(
        'staff',
        description="Role to assign (staff, admin, agent)"
    )

    model_config = {
        "json_schema_extra": {
            "description": "Base schema for staff invite link generation."
        }
    }


class StaffLinkGenerateSchema(BaseModel):
    """Schema for generating role-based invite tokens."""

    email: Optional[str] = Field(
        None, description="Optional email the token is intended for"
    )
    expires_in_days: int = Field(
        default=3,
        ge=1,
        le=90,
        description="Token expiry duration in days (1–90)"
    )

    model_config = {
        "json_schema_extra": {
            "description": "Schema for generating staff invite tokens."
        }
    }


class StaffLinkResponseSchema(BaseModel):
    """Response returned after generating a staff invite link."""

    detail: str = Field(..., description="Success message")
    token: str = Field(..., description="Generated role-based token")
    expires_at: str = Field(..., description="Token expiry timestamp (ISO format)")
    role: str = Field(..., description="Assigned role")

    model_config = {
        "json_schema_extra": {
            "description": "Response containing generated staff invite token details."
        }
    }


class SigninSchema(PinOrPasswordSchema):
    """Schema for user sign-in."""

    email: str = Field(..., description="User email address")

    model_config = {
        "json_schema_extra": {
            "description": "Schema for authenticating a user."
        }
    }


class Token(BaseModel):
    """Authentication token payload."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type (usually Bearer)")

    model_config = {
        "json_schema_extra": {
            "description": "Authentication token response schema."
        }
    }


class SigninResponse(UserResponseSchema):
    """Response returned after successful sign-in."""
    pass


class TokenData(BaseModel):
    """Decoded token data."""

    email: Optional[str] = Field(None, description="Email extracted from token")

    model_config = {
        "json_schema_extra": {
            "description": "Schema holding decoded token data."
        }
    }


class PasswordResetSchema(EmailEtCodeSchema, PinOrPasswordSchema):
    """Schema for resetting a user password or PIN."""
    #model_config = {
    #    "json_schema_extra": {
    #        "description": "Schema for password or PIN reset."
    #    }
    #}
    pass


class ConfirmPinOrPasswordChangeSchema(EmailEtCodeSchema):
    """Schema for confirming reset code before password/PIN change."""
    pass


class ConfirmPinOrPasswordChangeResponseSchema(BaseModel):
    """Response returned after successful reset-code confirmation."""

    detail: str = Field(..., description="Success message")
    x_expiration: str = Field(
        ...,
        description="Transient confirmation expiry timestamp in ISO format",
    )


class ApplyPinOrPasswordChangeSchema(PinOrPasswordSchema, Email):
    """Schema for applying password/PIN change after confirmation."""
    pass


class SendPasswordResetMail(BaseModel):
    """Response returned after sending password reset email."""

    message: str = Field(..., description="Success message")
    expiry: str = Field(..., description="Code expiry time in ISO format")

    model_config = {
        "json_schema_extra": {
            "description": "Response after sending password reset email."
        }
    }


class Email(BaseModel):
    """Schema containing only an email address."""

    email: str = Field(..., description="Email address")

    model_config = {
        "json_schema_extra": {
            "description": "Simple email-only payload."
        }
    }


class ProbeUserExistenceSchema(BaseModel):
    """Schema used to probe user existence."""

    username: str = Field(..., description="Username to check")
    email: str = Field(..., description="Email to check")

    model_config = {
        "json_schema_extra": {
            "description": "Schema for checking if a user exists."
        }
    }


class SendEmailCodeSchema(ProbeUserExistenceSchema):
    """Schema for sending an email code to an existing user."""
    pass


class PasscodeSchema(BaseModel):
    """Schema for submitting a 4-digit passcode."""

    pass_code: str = Field(..., description="4-digit passcode")

    model_config = {
        "json_schema_extra": {
            "description": "Schema for validating a passcode."
        }
    }
