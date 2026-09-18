from datetime import datetime

from pydantic import BaseModel, Field

from app.config import get_settings


class CategoryCreateRequest(BaseModel):
    """Request payload for creating a category."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Category title name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description text"
    )
    icon: str | None = Field(
        default=None, max_length=50, description="Emoji or icon identifier string"
    )
    color: str | None = Field(
        default=None, max_length=30, description="Hex accent color string"
    )


class CategoryUpdateRequest(BaseModel):
    """Request payload for updating an existing category."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=30)


class CategoryReorderRequest(BaseModel):
    """Request payload for re-ordering category display position."""

    ids: list[int] = Field(..., description="Ordered list of category integer IDs")


class CategoryResponse(BaseModel):
    """Response payload for category metadata."""

    id: int
    name: str
    slug: str
    description: str | None = None
    icon: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CATEGORY_ICON
    )
    color: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CATEGORY_COLOR
    )
    contentCount: int = 0
    order: int = 0
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


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

    id: int
    name: str
    slug: str
    description: str | None = None
    icon: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CATEGORY_ICON
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
