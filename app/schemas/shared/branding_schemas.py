from datetime import datetime

from pydantic import BaseModel, Field


class BrandingResponse(BaseModel):
    """
    Response DTO representing the creator's white-label app branding and studio identity.
    """

    creator_name: str | None = None
    tagline: str | None = None
    description: str | None = None
    banner_url: str | None = None
    logo_url: str | None = None
    updated_at: datetime | None = None


class BrandingUpdateRequest(BaseModel):
    """
    Request payload for updating creator branding identity text fields.
    Supports partial updates where only specified fields are modified.
    """

    creator_name: str | None = Field(
        None, max_length=255, description="Public creator / studio name"
    )
    tagline: str | None = Field(
        None, max_length=255, description="App tagline or slogan"
    )
    description: str | None = Field(
        None, description="Detailed channel or studio description"
    )


class BrandingLogoUploadResponse(BaseModel):
    """
    Response DTO returned after uploading a creator logo image.
    """

    logo_url: str


class BrandingBannerUploadResponse(BaseModel):
    """
    Response DTO returned after uploading a creator cover banner image.
    """

    banner_url: str
