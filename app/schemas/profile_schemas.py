from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SocialLinksSchema(BaseModel):
    """Nested schema for social media platform links."""
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    instagram: Optional[str] = None

class ProfileResponse(BaseModel):
    """Response DTO for creator profile information matching spec doc."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str  # Read-only identity display field
    bio: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Optional[SocialLinksSchema] = None
    updated_at: Optional[datetime] = None

class ProfileUpdateRequest(BaseModel):
    """Request payload for updating creator profile details (excluding email)."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    social_links: Optional[SocialLinksSchema] = None

class ProfilePhotoUploadResponse(BaseModel):
    """Response payload returned when uploading a new profile avatar photo."""
    avatar_url: str
