import logging

from fastapi import HTTPException, status

from app.repositories.category_repository import CategoryRepository
from app.schemas.category_schemas import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryOptionListResponse,
    CategoryOptionResponse,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    MobileCategoryResponse,
)

logger = logging.getLogger(__name__)


class CategoryService:
    """
    Business logic service for Creator Admin Category management operations.
    """

    def __init__(self):
        self.repo = CategoryRepository()

    def _to_category_response(self, cat, content_count: int = 0) -> CategoryResponse:
        return CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            icon=cat.icon or "📁",
            color=cat.color or "#3b82f6",
            contentCount=content_count,
            order=cat.display_order,
            createdAt=cat.created_at,
            updatedAt=cat.updated_at,
        )

    def list_mobile_categories(self):
        """
        Retrieves lightweight categories for mobile catalog filter chips.
        """
        categories = self.repo.list_public_mobile_categories()
        data = [
            MobileCategoryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                icon=c.icon or "📁",
                color=c.color or "#3b82f6",
            )
            for c in categories
        ]
        return {"data": data}

    def list_categories(self, user_id: int, simple: bool = False):
        """
        Retrieves categories for creator. If simple=True, returns lightweight dropdown options.
        """
        pairs = self.repo.list_categories(user_id, simple=simple)
        if simple:
            data = [
                CategoryOptionResponse(id=cat.id, name=cat.name, slug=cat.slug)
                for cat, _ in pairs
            ]
            return CategoryOptionListResponse(data=data)

        data = [self._to_category_response(cat, count) for cat, count in pairs]
        return CategoryListResponse(data=data)

    def create_category(
        self, user_id: int, req: CategoryCreateRequest
    ) -> CategoryResponse:
        """
        Creates a new category ensuring unique category name per creator.
        """
        existing = self.repo.get_category_by_name(req.name, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{req.name}' already exists",
            )

        cat = self.repo.create_category(user_id, req.model_dump())
        return self._to_category_response(cat, content_count=0)

    def update_category(
        self, category_id: int, user_id: int, req: CategoryUpdateRequest
    ) -> CategoryResponse:
        """
        Updates fields for an existing category asset.
        """
        cat = self.repo.get_category_by_id(category_id, user_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        if req.name and req.name.strip().lower() != cat.name.lower():
            existing = self.repo.get_category_by_name(req.name, user_id)
            if existing and existing.id != category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category name '{req.name}' is already used by another category",
                )

        updated_cat = self.repo.update_category(
            category_id, user_id, req.model_dump(exclude_unset=True)
        )
        # Fetch dynamic count
        pairs = self.repo.list_categories(user_id)
        count = next((cnt for c, cnt in pairs if c.id == category_id), 0)
        return self._to_category_response(updated_cat, content_count=count)

    def delete_category(self, category_id: int, user_id: int) -> dict:
        """
        Deletes a category asset.
        """
        cat = self.repo.get_category_by_id(category_id, user_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        self.repo.delete_category(category_id, user_id)
        return {"message": "Category deleted successfully"}

    def reorder_categories(self, user_id: int, req: CategoryReorderRequest) -> dict:
        """
        Updates display_order for category IDs.
        """
        if not req.ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one category ID must be provided",
            )

        self.repo.reorder_categories(user_id, req.ids)
        return {"message": "Category order updated"}
