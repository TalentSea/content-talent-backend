import logging

from fastapi import HTTPException, status

from app.config import get_settings
from app.repositories.featured_video_repository import FeaturedVideoRepository
from app.schemas.common_schemas import PaginatedResponse
from app.schemas.featured_video_schemas import (
    FeaturedAvailableVideoResponse,
    FeaturedVideoItemResponse,
    FeaturedVideoSyncRequest,
    FeaturedVideoSyncResponse,
)

logger = logging.getLogger(__name__)


class FeaturedVideoService:
    """
    Business logic layer for Admin Featured Videos curation matching 3-API State Sync design.
    """

    def __init__(self, repo: FeaturedVideoRepository | None = None) -> None:
        self.repo = repo or FeaturedVideoRepository()

    def _map_item(self, featured_row, video_row) -> FeaturedVideoItemResponse:
        return FeaturedVideoItemResponse(
            id=featured_row.id,
            video_id=video_row.id,
            position=featured_row.position,
            title=video_row.title,
            description=video_row.description,
            category=video_row.category,
            main_thumbnail_url=video_row.main_thumbnail_url,
            duration=video_row.duration,
            views=video_row.views or 0,
            likes=video_row.likes or 0,
            status=video_row.status,
            created_at=video_row.created_at,
        )

    def list_featured_videos(self, creator_id: int) -> list[FeaturedVideoItemResponse]:
        """
        Retrieves featured videos list for creator_id matching spec doc API 3.1.
        """
        rows = self.repo.get_featured_videos(creator_id)
        return [self._map_item(f_row, f_row.video) for f_row in rows]

    def sync_featured_videos(
        self, creator_id: int, payload: FeaturedVideoSyncRequest
    ) -> FeaturedVideoSyncResponse:
        """
        Full State Sync: Replaces creator's active featured videos in 1 atomic operation matching spec doc API 3.2.
        """
        max_allowed = get_settings().MAX_FEATURED_VIDEOS_PER_CREATOR
        if len(payload.video_ids) > max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot feature more than {max_allowed} videos per creator studio.",
            )

        updated_rows = self.repo.sync_featured_videos(
            creator_id=creator_id, video_ids=payload.video_ids
        )
        items = [self._map_item(f_row, f_row.video) for f_row in updated_rows]

        return FeaturedVideoSyncResponse(
            status="success",
            total_featured=len(items),
            items=items,
        )

    def get_available_videos_for_featured(
        self,
        creator_id: int,
        search: str | None = None,
        category: str | None = None,
        sort: str | None = "popular",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[FeaturedAvailableVideoResponse]:
        """
        Retrieves paginated available videos picker matching spec doc API 3.3.
        """
        videos, total = self.repo.get_available_videos_for_featured(
            creator_id=creator_id,
            search=search,
            category=category,
            sort=sort,
            page=page,
            limit=limit,
        )

        items = [
            FeaturedAvailableVideoResponse(
                id=v.id,
                title=v.title,
                category=v.category,
                duration=v.duration,
                main_thumbnail_url=v.main_thumbnail_url,
                views=v.views or 0,
                likes=v.likes or 0,
                created_at=v.created_at,
            )
            for v in videos
        ]

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )
