from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

HEX_COLOR_REGEX = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"


class ThemeColorsDTO(BaseModel):
    """
    Authoritative 9-token white-label studio theme color palette.
    """

    model_config = ConfigDict(populate_by_name=True)

    primaryColor: str = Field(
        default="#E50914",
        pattern=HEX_COLOR_REGEX,
        description="Primary brand accent color (e.g. See all links, category tags, CTAs)",
    )
    secondaryColor: str = Field(
        default="#5865F2",
        pattern=HEX_COLOR_REGEX,
        description="Secondary accent color (e.g. user avatar badge, subtle highlights)",
    )
    activeStateColor: str = Field(
        default="#5865F2",
        pattern=HEX_COLOR_REGEX,
        description="Active navigation tab and carousel indicator dot color",
    )
    mainBackgroundColor: str = Field(
        default="#000000",
        pattern=HEX_COLOR_REGEX,
        description="Main application background (pure dark OLED theme)",
    )
    cardBackgroundColor: str = Field(
        default="#12121A",
        pattern=HEX_COLOR_REGEX,
        description="Card and elevated surface background color",
    )
    primaryTextColor: str = Field(
        default="#FFFFFF",
        pattern=HEX_COLOR_REGEX,
        description="Primary high-contrast text color for headings and titles",
    )
    secondaryTextColor: str = Field(
        default="#9CA3AF",
        pattern=HEX_COLOR_REGEX,
        description="Secondary metadata text color for taglines, views, and dates",
    )
    mutedTextColor: str = Field(
        default="#6B7280",
        pattern=HEX_COLOR_REGEX,
        description="Muted caption text and inactive tab icon/label color",
    )
    buttonTextColor: str = Field(
        default="#FFFFFF",
        pattern=HEX_COLOR_REGEX,
        description="Text color for buttons and chips",
    )


class ThemeColorsUpdateRequest(BaseModel):
    """
    Request payload submitted by the Admin Web Portal when modifying the studio theme.
    Admin website sends only these 9 color properties.
    """

    model_config = ConfigDict(populate_by_name=True)

    primaryColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    secondaryColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    activeStateColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    mainBackgroundColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    cardBackgroundColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    primaryTextColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    secondaryTextColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    mutedTextColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)
    buttonTextColor: str | None = Field(None, pattern=HEX_COLOR_REGEX)


class BrandingResponse(BaseModel):
    """
    Response DTO representing the creator's white-label app branding, studio identity, and theme.
    """

    studio_name: str | None = None
    tagline: str | None = None
    description: str | None = None
    banner_url: str | None = None
    logo_url: str | None = None
    theme: ThemeColorsDTO = Field(default_factory=ThemeColorsDTO)
    updated_at: datetime | None = None


class BrandingUpdateRequest(BaseModel):
    """
    Request payload for updating creator branding identity text fields.
    Supports partial updates where only specified fields are modified.
    """

    studio_name: str | None = Field(
        None, max_length=255, description="Public creator studio / channel name"
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
