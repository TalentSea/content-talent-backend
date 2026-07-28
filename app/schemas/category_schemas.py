from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    contentCount: int = 0
    order: int
    createdAt: datetime

    class Config:
        from_attributes = True

class CategoryListResponse(BaseModel):
    data: List[CategoryResponse]

class CategoryReorderRequest(BaseModel):
    ids: List[str]
