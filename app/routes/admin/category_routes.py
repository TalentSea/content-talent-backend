from fastapi import APIRouter, status

from app.dependencies import CurrentAdmin, FormFile
from app.schemas.shared.category_schemas import (
    CategoryCreateRequest,
    CategoryCreateResponse,
    CategoryListResponse,
    CategoryOptionListResponse,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryThumbnailUploadResponse,
    CategoryUpdateRequest,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.shared.category_service import CategoryService

router = APIRouter(prefix="/api/v1/admin/categories", tags=["Admin Categories"])
category_service = CategoryService()


@router.get(
    "",
    response_model=CategoryOptionListResponse | CategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Creator Categories",
    description="Retrieves all content categories. Pass simple=true for lightweight UI dropdown options.",
)
def list_categories(current_user: CurrentAdmin, simple: bool = False):
    return category_service.list_categories(
        tenant_id=current_user["tenant_id"], simple=simple
    )


@router.post(
    "",
    response_model=CategoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category",
    description="Creates a new content category container with title, description, and hex color.",
)
def create_category(req: CategoryCreateRequest, current_user: CurrentAdmin):
    return category_service.create_category(tenant_id=current_user["tenant_id"], req=req)


@router.put(
    "/reorder",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Reorder Categories (Drag-and-Drop)",
    description="Persists new category display ordering after drag-and-drop actions in the Admin Portal UI.",
)
def reorder_categories(req: CategoryReorderRequest, current_user: CurrentAdmin):
    return category_service.reorder_categories(tenant_id=current_user["tenant_id"], req=req)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit Category",
    description="Updates textual metadata fields for an existing category asset.",
)
def update_category(
    category_id: int,
    req: CategoryUpdateRequest,
    current_user: CurrentAdmin,
):
    return category_service.update_category(
        category_id=category_id, tenant_id=current_user["tenant_id"], req=req
    )


@router.post(
    "/{category_id}/thumbnail/upload",
    response_model=CategoryThumbnailUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Category Thumbnail",
    description="Uploads a category logo/thumbnail image to Bunny Storage via server proxy.",
)
def upload_category_thumbnail(
    category_id: int, current_user: CurrentAdmin, file: FormFile
):
    return category_service.upload_category_thumbnail(
        tenant_id=current_user["tenant_id"], category_id=category_id, file=file
    )


@router.delete(
    "/{category_id}",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Category",
    description="Deletes a category asset and safely unassigns videos belonging to it.",
)
def delete_category(category_id: int, current_user: CurrentAdmin):
    return category_service.delete_category(
        category_id=category_id, tenant_id=current_user["tenant_id"]
    )
