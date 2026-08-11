from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CategoryCreateRequest(BaseModel):
    """Request payload for creating a category."""
    name: str = Field(..., min_length=1, max_length=100, description="Category title name")
    description: Optional[str] = Field(None, max_length=500, description="Optional description text")
    icon: Optional[str] = Field("📁", max_length=50, description="Emoji or icon identifier string")
    color: Optional[str] = Field("#3b82f6", max_length=30, description="Hex accent color string")

class CategoryUpdateRequest(BaseModel):
    """Request payload for updating an existing category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=30)

class CategoryReorderRequest(BaseModel):
    """Request payload for re-ordering category display position."""
    ids: List[int] = Field(..., description="Ordered list of category integer IDs")

class CategoryResponse(BaseModel):
    """Response payload for category metadata."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: str = "📁"
    color: str = "#3b82f6"
    contentCount: int = 0
    order: int = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class CategoryOptionResponse(BaseModel):
    """Lightweight response DTO for UI dropdown pickers when simple=true."""
    id: int
    name: str
    slug: str

class CategoryOptionListResponse(BaseModel):
    """Wrapper response for lightweight category dropdown options."""
    data: List[CategoryOptionResponse]

class MobileCategoryResponse(BaseModel):
    """Lightweight response DTO for mobile home feed category filter chips."""
    id: int
    name: str
    slug: str
    icon: str = "📁"
    color: str = "#3b82f6"

class MobileCategoryListResponse(BaseModel):
    """Wrapper response for mobile category list feed."""
    data: List[MobileCategoryResponse]

class CategoryListResponse(BaseModel):
    """Wrapper response for category list feed."""
    data: List[CategoryResponse]
