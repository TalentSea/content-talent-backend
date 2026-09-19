from fastapi import APIRouter, status

from app.dependencies import CurrentSubscriber
from app.schemas.shared.category_schemas import MobileCategoryListResponse
from app.services.shared.category_service import CategoryService

router = APIRouter(prefix="/api/v1/mobile/categories", tags=["Mobile Categories"])
category_service = CategoryService()


@router.get(
    "",
    response_model=MobileCategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Mobile Category Filter Feed",
    description="Retrieves active categories for horizontal filter chips on mobile home feed. Accessible by Guests and Subscribers.",
)
def list_mobile_categories(current_subscriber: CurrentSubscriber):
    return category_service.list_mobile_categories(
        creator_id=current_subscriber.get("creator_id")
    )
