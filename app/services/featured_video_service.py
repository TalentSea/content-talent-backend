import logging

from fastapi import HTTPException, status

from app.repositories.featured_video_repository import FeaturedVideoRepository
from app.schemas.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.schemas.featured_video_schemas import (
    FeaturedAvailableVideoResponse,
    FeaturedVideoAddRequest,
    FeaturedVideoAddResponse,
    FeaturedVideoBulkDeleteRequest,
    FeaturedVideoItemResponse,
    FeaturedVideoReorderRequest,
)

logger = logging.getLogger(__name__)


class FeaturedVideoService:
    """
    Business logic layer orchestrating creator home screen featured video curation.
    """

    def __init__(self, repo: FeaturedVideoRepository | None = None) -> None:
        self.repo = repo or FeaturedVideoRepository()

    def list_featured_videos(self, creator_id: int) -> list[FeaturedVideoItemResponse]:
        """
        Retrieves featured video list for creator_id matching spec API 3.1.
        """
        featured_list = self.repo.get_featured_videos(creator_id)
        items = [
            FeaturedVideoItemResponse(
                id=fv.id,
                video_id=v.id,
                position=fv.position,
                title=v.title,
                category=v.category,
                main_thumbnail_url=v.main_thumbnail_url,
                duration=v.duration,
                views=v.views or 0,
                likes=v.likes or 0,
                status=v.status,
                created_at=v.created_at,
            )
            for fv, v in [(item, item.video) for item in featured_list]
        ]
        return items

    def add_featured_videos(
        self, creator_id: int, payload: FeaturedVideoAddRequest
    ) -> FeaturedVideoAddResponse:
        """
        Adds video IDs to creator's featured list matching spec API 3.2.
        """
        try:
            added_count, new_total = self.repo.add_featured_videos(
                creator_id=creator_id, video_ids=payload.video_ids
            )
            if added_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid un-featured videos found belonging to creator.",
                )
            return FeaturedVideoAddResponse(
                status="success",
                added_count=added_count,
                total_featured=new_total,
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)
            )

    def reorder_featured_videos(
        self, creator_id: int, payload: FeaturedVideoReorderRequest
    ) -> ActionSuccessResponse:
        """
        Reorders featured video positions matching spec API 3.3.
        """
        self.repo.reorder_featured_videos(
            creator_id=creator_id, video_ids=payload.video_ids
        )
        return ActionSuccessResponse(status="success")

    def delete_featured_video(
        self, creator_id: int, video_id: int
    ) -> ActionSuccessResponse:
        """
        Deletes video from featured list matching spec API 3.4.
        """
        deleted = self.repo.delete_featured_video(
            creator_id=creator_id, video_id=video_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} is not in creator's featured list.",
            )
        return ActionSuccessResponse(status="success")

    def bulk_delete_featured_videos(
        self, creator_id: int, payload: FeaturedVideoBulkDeleteRequest
    ) -> ActionSuccessResponse:
        """
        Bulk deletes multiple videos from creator's featured list matching spec API 3.4.
        """
        deleted_count = self.repo.bulk_delete_featured_videos(
            creator_id=creator_id, video_ids=payload.video_ids
        )
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="None of the specified video IDs were in creator's featured list.",
            )
        return ActionSuccessResponse(status="success")

    def get_available_videos_for_featured(
        self,
        creator_id: int,
        search: str | None = None,
        category: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[FeaturedAvailableVideoResponse]:
        """
        Retrieves paginated available published creator videos for featured picker matching spec API 3.5.
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
