from pydantic import BaseModel, EmailStr, Field


class AdminLoginRequest(BaseModel):
    """
    Request payload for Creator Admin login.
    """

    email: EmailStr = Field(..., description="Creator's registered login email")
    password: str = Field(..., min_length=8, description="Account password (min 8 characters)")


class AdminSummaryResponse(BaseModel):
    """
    Core creator session profile returned on login and GET /me for rapid dashboard and navbar hydration.
    """

    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    studio_name: str | None = None
    avatar_url: str | None = None


class AdminLoginResponse(BaseModel):
    """
    Response payload returned upon successful Creator Admin login.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    admin: AdminSummaryResponse


class AdminTokenResponse(BaseModel):
    """
    Response payload returned upon silent token refresh.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
