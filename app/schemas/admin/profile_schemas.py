from datetime import datetime

from pydantic import BaseModel


class SocialLinksSchema(BaseModel):
    """Nested schema for social media platform links."""

    twitter: str | None = None
    youtube: str | None = None
    instagram: str | None = None


class ProfileResponse(BaseModel):
    """Response DTO for creator profile information matching spec doc."""

    first_name: str | None = None
    last_name: str | None = None
    email: str  # Read-only identity display field
    bio: str | None = None
    website: str | None = None
    phone: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    social_links: SocialLinksSchema | None = None
    updated_at: datetime | None = None


class ProfileUpdateRequest(BaseModel):
    """Request payload for updating creator profile details (excluding email)."""

    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    website: str | None = None
    phone: str | None = None
    location: str | None = None
    social_links: SocialLinksSchema | None = None


class ProfilePhotoUploadResponse(BaseModel):
    """Response payload returned when uploading a new profile avatar photo."""

    avatar_url: str
