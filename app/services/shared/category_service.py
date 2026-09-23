import logging
import time

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.shared.category_repository import CategoryRepository
from app.schemas.shared.category_schemas import (
    CategoryCreateRequest,
    CategoryCreateResponse,
    CategoryListResponse,
    CategoryOptionListResponse,
    CategoryOptionResponse,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryThumbnailUploadResponse,
    CategoryUpdateRequest,
    MobileCategoryResponse,
)
from app.utils.bunny_client import delete_bunny_storage_file
from app.utils.image_uploader import validate_and_upload_image

logger = logging.getLogger(__name__)


class CategoryService:
    """
    Business logic service for Tenant Category management operations.
    """

    def __init__(self):
        self.repo = CategoryRepository()

    def _to_category_response(self, cat, content_count: int = 0) -> CategoryResponse:
        settings = get_settings()
        return CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            thumbnailUrl=cat.thumbnail_url or "",
            color=cat.color or settings.DEFAULT_CATEGORY_COLOR,
            contentCount=content_count,
            order=cat.display_order,
            createdAt=cat.created_at,
            updatedAt=cat.updated_at,
        )

    def list_mobile_categories(self, tenant_id: int | None = None):
        """
        Retrieves lightweight categories for mobile catalog filter chips.
        """
        settings = get_settings()
        categories = self.repo.list_public_mobile_categories(tenant_id)
        data = [
            MobileCategoryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
                thumbnailUrl=c.thumbnail_url or "",
                color=c.color or settings.DEFAULT_CATEGORY_COLOR,
            )
            for c in categories
        ]
        return {"data": data}

    def list_categories(self, tenant_id: int | None = None, simple: bool = False):
        """
        Retrieves categories for tenant. If simple=True, returns lightweight dropdown options.
        """
        if not tenant_id:
            return CategoryOptionListResponse(data=[]) if simple else CategoryListResponse(data=[])

        pairs = self.repo.list_categories(tenant_id, simple=simple)
        if simple:
            data = [
                CategoryOptionResponse(id=cat.id, name=cat.name, slug=cat.slug)
                for cat, _ in pairs
            ]
            return CategoryOptionListResponse(data=data)

        data = [self._to_category_response(cat, count) for cat, count in pairs]
        return CategoryListResponse(data=data)

    def create_category(
        self, tenant_id: int, req: CategoryCreateRequest
    ) -> CategoryCreateResponse:
        """
        Creates a new category container ensuring unique category name per tenant.
        """
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context required")

        existing = self.repo.get_category_by_name(req.name, tenant_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{req.name}' already exists",
            )

        cat = self.repo.create_category(tenant_id, req.model_dump())
        settings = get_settings()
        return CategoryCreateResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            color=cat.color or settings.DEFAULT_CATEGORY_COLOR,
            order=cat.display_order,
            createdAt=cat.created_at,
        )

    def update_category(
        self, category_id: int, tenant_id: int, req: CategoryUpdateRequest
    ) -> CategoryResponse:
        """
        Updates fields for an existing category asset.
        """
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context required")

        cat = self.repo.get_category_by_id(category_id, tenant_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        if req.name and req.name.strip().lower() != cat.name.lower():
            existing = self.repo.get_category_by_name(req.name, tenant_id)
            if existing and existing.id != category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category name '{req.name}' is already used by another category",
                )

        updated_cat = self.repo.update_category(
            category_id, tenant_id, req.model_dump(exclude_unset=True)
        )
        pairs = self.repo.list_categories(tenant_id)
        count = next((cnt for c, cnt in pairs if c.id == category_id), 0)
        return self._to_category_response(updated_cat, content_count=count)

    def upload_category_thumbnail(
        self, category_id: int, file: UploadFile, tenant_id: int
    ) -> CategoryThumbnailUploadResponse:
        """
        Uploads and validates a category thumbnail image to Bunny Storage.
        """
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context required")

        cat = self.repo.get_category_by_id(category_id, tenant_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        settings = get_settings()
        timestamp = int(time.time())

        thumbnail_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/categories/cat_{category_id}_{timestamp}",
            max_size_mb=settings.MAX_THUMBNAIL_SIZE_MB,
            old_file_url=cat.thumbnail_url,
            old_file_storage_folder="assets/categories",
        )

        self.repo.update_category(
            category_id, tenant_id, {"thumbnail_url": thumbnail_url}
        )

        return CategoryThumbnailUploadResponse(thumbnail_url=thumbnail_url)

    def delete_category(self, category_id: int, tenant_id: int) -> dict:
        """
        Deletes a category asset and cleans up its thumbnail from Bunny Storage.
        """
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context required")

        cat = self.repo.get_category_by_id(category_id, tenant_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        if cat.thumbnail_url:
            try:
                filename = cat.thumbnail_url.split("?")[0].split("/")[-1]
                storage_path = f"assets/categories/{filename}"
                delete_bunny_storage_file(storage_path)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to delete Bunny Storage image for category %s: %s",
                    category_id,
                    e,
                )

        self.repo.delete_category(category_id, tenant_id)
        return {"message": "Category deleted successfully"}

    def reorder_categories(
        self, req: CategoryReorderRequest, tenant_id: int
    ) -> dict:
        """
        Updates display_order for category IDs.
        """
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context required")

        if not req.ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one category ID must be provided",
            )

        self.repo.reorder_categories(tenant_id, req.ids)
        return {"message": "Category order updated"}
