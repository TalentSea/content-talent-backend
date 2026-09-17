import logging

from fastapi import HTTPException, status
from peewee import fn

from app.config import get_settings
from app.models.video import VideoLike
from app.repositories.admin.featured_video_repository import FeaturedVideoRepository
from app.schemas.admin.featured_video_schemas import (
    FeaturedAvailableVideoResponse,
    FeaturedVideoItemResponse,
    FeaturedVideoSyncRequest,
    FeaturedVideoSyncResponse,
)
from app.schemas.shared.common_schemas import PaginatedResponse

logger = logging.getLogger(__name__)


class FeaturedVideoService:
    """
    Business logic layer for Admin Featured Videos curation matching 3-API State Sync design.
    """

    def __init__(self, repo: FeaturedVideoRepository | None = None) -> None:
        self.repo = repo or FeaturedVideoRepository()

    def _map_item(
        self, featured_row, video_row, likes: int | None = None
    ) -> FeaturedVideoItemResponse:
        likes_count = (
            likes
            if likes is not None
            else (video_row.likes.count() if hasattr(video_row.likes, "count") else 0)
        )
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
            likes=likes_count,
            status=video_row.status,
            created_at=video_row.created_at,
        )

    def list_featured_videos(self, creator_id: int) -> list[FeaturedVideoItemResponse]:
        """
        Retrieves featured videos list for creator_id matching spec doc API 3.1.
        """
        rows = self.repo.get_featured_videos(creator_id)
        video_ids = [f_row.video.id for f_row in rows]
        likes_map: dict[int, int] = {}
        if video_ids:
            counts = (
                VideoLike.select(VideoLike.video, fn.COUNT(VideoLike.id))
                .where(VideoLike.video.in_(video_ids))
                .group_by(VideoLike.video)
                .tuples()
            )
            likes_map = {vid: cnt for vid, cnt in counts}

        return [
            self._map_item(f_row, f_row.video, likes=likes_map.get(f_row.video.id, 0))
            for f_row in rows
        ]

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
        video_ids = [f_row.video.id for f_row in updated_rows]
        likes_map: dict[int, int] = {}
        if video_ids:
            counts = (
                VideoLike.select(VideoLike.video, fn.COUNT(VideoLike.id))
                .where(VideoLike.video.in_(video_ids))
                .group_by(VideoLike.video)
                .tuples()
            )
            likes_map = {vid: cnt for vid, cnt in counts}

        items = [
            self._map_item(f_row, f_row.video, likes=likes_map.get(f_row.video.id, 0))
            for f_row in updated_rows
        ]

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

        video_ids = [v.id for v in videos]
        likes_map: dict[int, int] = {}
        if video_ids:
            counts = (
                VideoLike.select(VideoLike.video, fn.COUNT(VideoLike.id))
                .where(VideoLike.video.in_(video_ids))
                .group_by(VideoLike.video)
                .tuples()
            )
            likes_map = {vid: cnt for vid, cnt in counts}

        items = [
            FeaturedAvailableVideoResponse(
                id=v.id,
                title=v.title,
                category=v.category,
                duration=v.duration,
                main_thumbnail_url=v.main_thumbnail_url,
                views=v.views or 0,
                likes=likes_map.get(v.id, 0),
                created_at=v.created_at,
            )
            for v in videos
        ]

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )
