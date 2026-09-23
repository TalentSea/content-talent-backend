from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TenantCreateRequest(BaseModel):
    """
    Payload for creating a new brand/tenant along with its initial owner admin user.
    """

    name: str = Field(..., max_length=255, description="Tenant brand / studio name")
    tagline: str | None = Field(None, max_length=255, description="Optional brand slogan")
    description: str | None = Field(None, description="Studio description")
    admin_email: EmailStr = Field(..., description="First owner admin email")
    admin_password: str = Field(..., min_length=8, description="Initial owner admin password")
    admin_first_name: str = Field(..., max_length=100, description="Owner first name")
    admin_last_name: str = Field(..., max_length=100, description="Owner last name")
    admin_phone: str | None = Field(None, max_length=50, description="Owner phone number")


class TenantStatusUpdateRequest(BaseModel):
    """
    Payload for modifying tenant activation status.
    """

    is_active: bool
    deactivation_reason: str | None = None


class TenantCreateResponse(BaseModel):
    """
    Response returned upon successfully provisioning a new Tenant studio.
    Excludes visual branding assets and deactivation metadata.
    """

    id: int
    owner_id: int
    name: str
    slug: str
    tagline: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime


class TenantResponse(BaseModel):
    """
    Public and admin representation of a white-label studio tenant.
    """

    id: int
    name: str
    slug: str
    tagline: str | None = None
    description: str | None = None
    is_active: bool
    logo_url: str | None = None
    deactivation_reason: str | None = None
    deactivated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    admins_count: int = 0
    videos_count: int = 0
    subscribers_count: int = 0


class TenantListItem(BaseModel):
    """
    Lightweight tenant representation for listing, context switching, and selection.
    """

    id: int
    name: str
    is_active: bool



class AdminUserCreateRequest(BaseModel):
    """
    Payload for provisioning a new admin user within a tenant.
    """

    email: EmailStr = Field(..., description="Admin login email")
    password: str = Field(..., min_length=8, description="Initial password")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: str | None = Field(None, max_length=50)


class AdminUserStatusUpdateRequest(BaseModel):
    """
    Payload for activating or suspending an admin user.
    """

    is_active: bool


class AdminUserResponse(BaseModel):
    """
    Representation of an admin user account.
    """

    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    role: str
    is_owner: bool
    is_active: bool
    avatar_url: str | None = None
    created_at: datetime
