from typing import Union
from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_admin
from app.schemas.category_schemas import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryListResponse,
    CategoryOptionListResponse
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/admin/categories", tags=["Admin Categories"])
category_service = CategoryService()

@router.get(
    "",
    response_model=Union[CategoryOptionListResponse, CategoryListResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Creator Categories",
    description="Retrieves all content categories. Pass simple=true for lightweight UI dropdown options."
)
def list_categories(
    simple: bool = False,
    current_user: dict = Depends(get_current_admin)
):
    return category_service.list_categories(user_id=current_user["user_id"], simple=simple)

@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category",
    description="Creates a new content category with title, description, emoji icon, and hex color."
)
def create_category(
    req: CategoryCreateRequest,
    current_user: dict = Depends(get_current_admin)
):
    return category_service.create_category(user_id=current_user["user_id"], req=req)

@router.put(
    "/reorder",
    status_code=status.HTTP_200_OK,
    summary="Reorder Categories (Drag-and-Drop)",
    description="Persists new category display ordering after drag-and-drop actions in the Admin Portal UI."
)
def reorder_categories(
    req: CategoryReorderRequest,
    current_user: dict = Depends(get_current_admin)
):
    return category_service.reorder_categories(user_id=current_user["user_id"], req=req)

@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit Category",
    description="Updates textual metadata fields for an existing category asset."
)
def update_category(
    category_id: int,
    req: CategoryUpdateRequest,
    current_user: dict = Depends(get_current_admin)
):
    return category_service.update_category(category_id=category_id, user_id=current_user["user_id"], req=req)

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Category",
    description="Deletes a category asset and safely unassigns videos belonging to it."
)
def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_admin)
):
    return category_service.delete_category(category_id=category_id, user_id=current_user["user_id"])
