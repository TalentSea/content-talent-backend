from fastapi import APIRouter, Query, status

from app.dependencies import CurrentAdmin
from app.schemas.common_schemas import PaginatedResponse
from app.schemas.featured_video_schemas import (
    FeaturedAvailableVideoResponse,
    FeaturedVideoItemResponse,
    FeaturedVideoSyncRequest,
    FeaturedVideoSyncResponse,
)
from app.services.featured_video_service import FeaturedVideoService

router = APIRouter(prefix="/api/v1/admin/featured-videos", tags=["Admin Featured Videos"])
service = FeaturedVideoService()


@router.get(
    "",
    response_model=list[FeaturedVideoItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List Featured Videos",
    description="Retrieves all videos currently featured by the authenticated creator, ordered by position ascending.",
)
def list_featured_videos(current_user: CurrentAdmin) -> list[FeaturedVideoItemResponse]:
    return service.list_featured_videos(current_user["user_id"])


@router.put(
    "",
    response_model=FeaturedVideoSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Full State Sync Featured Videos",
    description="Replaces and synchronizes the active featured videos list for the creator (Add, Reorder, Delete in 1 API).",
)
def sync_featured_videos(
    payload: FeaturedVideoSyncRequest,
    current_user: CurrentAdmin,
) -> FeaturedVideoSyncResponse:
    return service.sync_featured_videos(current_user["user_id"], payload)


@router.get(
    "/available",
    response_model=PaginatedResponse[FeaturedAvailableVideoResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Available Videos Picker",
    description="Retrieves paginated list of creator's published videos that are not currently featured (picker modal).",
)
def get_available_videos_for_featured(
    current_user: CurrentAdmin,
    search: str | None = Query(None, description="Search available videos by title substring"),
    category: str | None = Query(None, description="Filter available videos by category slug/name"),
    sort: str | None = Query("popular", description="Sort order: popular, most_viewed, oldest, newest"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[FeaturedAvailableVideoResponse]:
    return service.get_available_videos_for_featured(
        creator_id=current_user["user_id"],
        search=search,
        category=category,
        sort=sort,
        page=page,
        limit=limit,
    )
