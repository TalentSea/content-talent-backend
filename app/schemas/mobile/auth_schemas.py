from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    """
    Dedicated payload for Google OIDC Sign-In.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    id_token: str = Field(..., description="Google OIDC id_token JWT string")
    device_info: str | None = Field(
        None, description="Client device description string"
    )


class FacebookAuthRequest(BaseModel):
    """
    Dedicated payload for Facebook OAuth 2.0 Sign-In.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    access_token: str = Field(..., description="Facebook OAuth 2.0 access_token string")
    device_info: str | None = Field(
        None, description="Client device description string"
    )


class GuestAuthRequest(BaseModel):
    """
    Dedicated payload for Anonymous Guest Session ("Skip Signup").
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    device_id: str = Field(..., description="Unique mobile device hardware ID")
    device_info: str | None = Field(
        None, description="Client device description string"
    )


class MobileRegisterRequest(BaseModel):
    """
    Payload to initiate subscriber email registration and dispatch in-app OTP.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    name: str = Field(..., min_length=2, max_length=100, description="Full name of subscriber")
    email: EmailStr = Field(..., description="Subscriber email address")
    password: str = Field(..., min_length=6, max_length=128, description="Secure account password")
    device_info: str | None = Field(None, description="Client device description string")


class VerifyRegistrationRequest(BaseModel):
    """
    Payload to submit 6-digit OTP and complete subscriber registration or smart linking.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    email: EmailStr = Field(..., description="Subscriber email address")
    code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$", description="6-digit verification code")
    device_info: str | None = Field(None, description="Client device description string")


class MobileLoginRequest(BaseModel):
    """
    Payload for native email and password authentication.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    email: EmailStr = Field(..., description="Subscriber login email")
    password: str = Field(..., min_length=1, description="Account password")
    device_info: str | None = Field(None, description="Client device description string")


class ForgotPasswordRequest(BaseModel):
    """
    Payload to initiate password reset and send in-app 6-digit OTP code.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    email: EmailStr = Field(..., description="Subscriber registered email")


class VerifyResetCodeRequest(BaseModel):
    """
    Payload to verify 6-digit password reset OTP and obtain stateless reset token.
    """

    tenant_id: int = Field(..., description="Target tenant studio ID")
    email: EmailStr = Field(..., description="Subscriber registered email")
    code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$", description="6-digit verification code")


class VerifyResetCodeResponse(BaseModel):
    """
    Response containing stateless signed JWT reset token.
    """

    status: str = "success"
    reset_token: str = Field(..., description="Stateless signed JWT token for password reset (10m expiry)")


class ResetPasswordRequest(BaseModel):
    """
    Payload to set new password using stateless reset token.
    """

    reset_token: str = Field(..., description="Stateless signed JWT reset token obtained from verify-reset-code")
    new_password: str = Field(..., min_length=6, max_length=128, description="New strong password")


class RefreshTokenRequest(BaseModel):
    """
    Payload for silent access token refresh or session logout.
    """

    refresh_token: str = Field(..., description="Active session refresh token string")


class UserProfileResponse(BaseModel):
    """
    User profile DTO matching social authentication spec.
    """

    id: int
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    provider: str
    role: str
    created_at: datetime | None = None


class AuthTokenResponse(BaseModel):
    """
    OAuth 2.0 JWT Token response object.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user: UserProfileResponse
