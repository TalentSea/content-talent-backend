from typing import Optional
from fastapi import APIRouter, Depends, status

from app.dependencies import get_optional_subscriber
from app.schemas.category_schemas import MobileCategoryListResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/mobile/categories", tags=["Mobile Categories"])
category_service = CategoryService()

@router.get(
    "",
    response_model=MobileCategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Mobile Category Filter Feed",
    description="Retrieves active categories for horizontal filter chips on mobile home feed. Accessible by Guests and Subscribers."
)
def list_mobile_categories(
    current_user: Optional[dict] = Depends(get_optional_subscriber)
):
    return category_service.list_mobile_categories()
