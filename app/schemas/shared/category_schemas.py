from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.config import get_settings


class CategoryCreateRequest(BaseModel):
    """Request payload for creating a category."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Category title name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description text"
    )
    color: str | None = Field(
        default=None, max_length=30, description="Hex accent color string"
    )


class CategoryUpdateRequest(BaseModel):
    """Request payload for updating an existing category."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    color: str | None = Field(None, max_length=30)


class CategoryReorderRequest(BaseModel):
    """Request payload for re-ordering category display position."""

    ids: list[int] = Field(..., description="Ordered list of category integer IDs")


class CategoryThumbnailUploadResponse(BaseModel):
    """Response DTO returned after uploading a category thumbnail image."""

    thumbnail_url: str


class CategoryCreateResponse(BaseModel):
    """Response payload returned when a category is created matching spec doc API 2 and Playlist pattern."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    slug: str
    description: str | None = None
    color: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CATEGORY_COLOR
    )
    order: int = Field(0, validation_alias=AliasChoices("order", "display_order"))
    created_at: datetime | None = Field(
        None, validation_alias=AliasChoices("created_at", "createdAt")
    )


class CategoryResponse(BaseModel):
    """Response payload for category metadata."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    slug: str
    description: str | None = None
    thumbnail_url: str = Field(
        "", validation_alias=AliasChoices("thumbnail_url", "thumbnailUrl")
    )
    color: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CATEGORY_COLOR
    )
    content_count: int = Field(
        0, validation_alias=AliasChoices("content_count", "contentCount")
    )
    order: int = Field(0, validation_alias=AliasChoices("order", "display_order"))
    created_at: datetime | None = Field(
        None, validation_alias=AliasChoices("created_at", "createdAt")
    )
    updated_at: datetime | None = Field(
        None, validation_alias=AliasChoices("updated_at", "updatedAt")
    )


class CategoryOptionResponse(BaseModel):
    """Lightweight response DTO for UI dropdown pickers when simple=true."""

    id: int
    name: str
    slug: str


class CategoryOptionListResponse(BaseModel):
    """Wrapper response for lightweight category dropdown options."""

    data: list[CategoryOptionResponse]


class MobileCategoryResponse(BaseModel):
    """Lightweight response DTO for mobile home feed category filter chips."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    slug: str
    description: str | None = None
    thumbnail_url: str = Field(
        "", validation_alias=AliasChoices("thumbnail_url", "thumbnailUrl")
    )
    color: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CATEGORY_COLOR
    )


class MobileCategoryListResponse(BaseModel):
    """Wrapper response for mobile category list feed."""

    data: list[MobileCategoryResponse]


class CategoryListResponse(BaseModel):
    """Wrapper response for category list feed."""

    data: list[CategoryResponse]
