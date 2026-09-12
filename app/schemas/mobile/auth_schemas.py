from datetime import datetime

from pydantic import BaseModel, Field


class GoogleAuthRequest(BaseModel):
    """
    Dedicated payload for Google OIDC Sign-In.
    """

    creator_id: int = Field(..., description="Target Admin Creator studio ID")
    id_token: str = Field(..., description="Google OIDC id_token JWT string")
    device_info: str | None = Field(
        None, description="Client device description string"
    )


class FacebookAuthRequest(BaseModel):
    """
    Dedicated payload for Facebook OAuth 2.0 Sign-In.
    """

    creator_id: int = Field(..., description="Target Admin Creator studio ID")
    access_token: str = Field(..., description="Facebook OAuth 2.0 access_token string")
    device_info: str | None = Field(
        None, description="Client device description string"
    )


class GuestAuthRequest(BaseModel):
    """
    Dedicated payload for Anonymous Guest Session ("Skip Signup").
    """

    creator_id: int = Field(..., description="Target Admin Creator studio ID")
    device_id: str = Field(..., description="Unique mobile device hardware ID")
    device_info: str | None = Field(
        None, description="Client device description string"
    )


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
