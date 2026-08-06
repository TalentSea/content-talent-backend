from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class GoogleAuthRequest(BaseModel):
    """
    Dedicated payload for Google OIDC Sign-In.
    """
    id_token: str = Field(..., description="Google OIDC id_token JWT string")
    device_info: Optional[str] = Field(None, description="Client device description string")

class FacebookAuthRequest(BaseModel):
    """
    Dedicated payload for Facebook OAuth 2.0 Sign-In.
    """
    access_token: str = Field(..., description="Facebook OAuth 2.0 access_token string")
    device_info: Optional[str] = Field(None, description="Client device description string")

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
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: str
    role: str
    created_at: Optional[datetime] = None

class AuthTokenResponse(BaseModel):
    """
    OAuth 2.0 JWT Token response object.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user: UserProfileResponse
