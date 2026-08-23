from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_admin
from app.schemas.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.schemas.featured_video_schemas import (
    FeaturedAvailableVideoResponse,
    FeaturedVideoAddRequest,
    FeaturedVideoAddResponse,
    FeaturedVideoBulkDeleteRequest,
    FeaturedVideoItemResponse,
    FeaturedVideoReorderRequest,
)
from app.services.featured_video_service import FeaturedVideoService

router = APIRouter(prefix="/api/v1/admin/featured-videos", tags=["Admin Featured Videos"])
service = FeaturedVideoService()


@router.get(
    "",
    response_model=list[FeaturedVideoItemResponse],
    summary="List Featured Videos",
    description="Retrieves all videos currently featured by the authenticated creator, ordered by position ascending.",
)
def list_featured_videos(
    current_admin: dict = Depends(get_current_admin),
) -> list[FeaturedVideoItemResponse]:
    return service.list_featured_videos(current_admin["user_id"])


@router.post(
    "",
    response_model=FeaturedVideoAddResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Featured Videos",
    description="Adds video IDs to creator's featured carousel list. Appends new items at next position sequence (max 10 cap).",
)
def add_featured_videos(
    payload: FeaturedVideoAddRequest,
    current_admin: dict = Depends(get_current_admin),
) -> FeaturedVideoAddResponse:
    return service.add_featured_videos(current_admin["user_id"], payload)


@router.put(
    "/reorder",
    response_model=ActionSuccessResponse,
    summary="Reorder Featured Videos",
    description="Batch updates position sequence for featured videos matching visual sequence.",
)
def reorder_featured_videos(
    payload: FeaturedVideoReorderRequest,
    current_admin: dict = Depends(get_current_admin),
) -> ActionSuccessResponse:
    return service.reorder_featured_videos(current_admin["user_id"], payload)


@router.delete(
    "",
    response_model=ActionSuccessResponse,
    summary="Bulk Remove Featured Videos",
    description="Removes multiple selected videos from creator's featured list and compacts position sequence.",
)
def bulk_delete_featured_videos(
    payload: FeaturedVideoBulkDeleteRequest,
    current_admin: dict = Depends(get_current_admin),
) -> ActionSuccessResponse:
    return service.bulk_delete_featured_videos(current_admin["user_id"], payload)


@router.delete(
    "/{video_id}",
    response_model=ActionSuccessResponse,
    summary="Remove Single Featured Video",
    description="Removes a video from the creator's featured list and compacts remaining positions.",
)
def delete_featured_video(
    video_id: int,
    current_admin: dict = Depends(get_current_admin),
) -> ActionSuccessResponse:
    return service.delete_featured_video(current_admin["user_id"], video_id)


@router.get(
    "/available",
    response_model=PaginatedResponse[FeaturedAvailableVideoResponse],
    summary="Available Videos Picker",
    description="Retrieves paginated published creator videos available to be added to featured list.",
)
def get_available_videos_for_featured(
    search: str | None = Query(None, description="Title search substring"),
    category: str | None = Query(None, description="Filter by category slug"),
    sort: str = Query("newest", description="Sorting criteria: newest, oldest, popular (or most_viewed), most_liked"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: dict = Depends(get_current_admin),
) -> PaginatedResponse[FeaturedAvailableVideoResponse]:
    return service.get_available_videos_for_featured(
        creator_id=current_admin["user_id"],
        search=search,
        category=category,
        sort=sort,
        page=page,
        limit=limit,
    )
