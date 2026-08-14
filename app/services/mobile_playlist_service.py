import logging
import math

from fastapi import HTTPException, status

from app.repositories.mobile_playlist_repository import MobilePlaylistRepository
from app.schemas.mobile_playlist_schemas import (
    MobilePlaylistDetailsResponse,
    MobilePlaylistListItemResponse,
    MobilePlaylistListResponse,
    MobilePlaylistVideoItemResponse,
    MobilePlaylistVideosResponse,
)
from app.schemas.mobile_video_schemas import WatchProgressResponse

logger = logging.getLogger(__name__)


class MobilePlaylistService:
    """
    Business logic layer for Mobile Subscriber Playlist Feed & Video Streaming operations.
    """

    def __init__(self):
        self.repo = MobilePlaylistRepository()

    def list_public_playlists(
        self,
        search: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> MobilePlaylistListResponse:
        """
        Retrieves paginated public creator playlists feed matching spec API 1.
        """
        results, total = self.repo.list_public_playlists(
            search=search, sort=sort, page=page, limit=limit
        )

        items = [
            MobilePlaylistListItemResponse(
                id=playlist.id,
                name=playlist.name,
                thumbnail_url=playlist.thumbnail_url,
                video_count=video_count,
                created_at=playlist.created_at,
            )
            for playlist, video_count in results
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return MobilePlaylistListResponse(
            total=total, page=page, limit=limit, total_pages=total_pages, items=items
        )

    def get_playlist_details(
        self,
        playlist_id: int,
        subscriber_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> MobilePlaylistDetailsResponse:
        """
        Retrieves single public playlist header alongside paginated video items matching spec API 2.
        """
        playlist = self.repo.get_public_playlist_by_id(playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        video_items, total = self.repo.get_playlist_videos_with_subscriber_overlay(
            playlist=playlist, subscriber_id=subscriber_id, page=page, limit=limit
        )

        formatted_video_items: list[MobilePlaylistVideoItemResponse] = []
        for item in video_items:
            v = item["video"]
            wp_dict = item["watch_progress"]
            watch_progress = (
                WatchProgressResponse(
                    last_position_seconds=wp_dict["last_position_seconds"],
                    completion_percentage=wp_dict["completion_percentage"],
                )
                if wp_dict
                else None
            )

            formatted_video_items.append(
                MobilePlaylistVideoItemResponse(
                    id=v.id,
                    title=v.title,
                    category=v.category,
                    duration=v.duration,
                    main_thumbnail_url=v.main_thumbnail_url,
                    views=v.views or 0,
                    likes=item["likes"],
                    is_liked=item["is_liked"],
                    is_saved=item["is_saved"],
                    watch_progress=watch_progress,
                    order=item["order"],
                    created_at=v.created_at,
                )
            )

        total_pages = math.ceil(total / limit) if total > 0 else 1

        videos_envelope = MobilePlaylistVideosResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=formatted_video_items,
        )

        return MobilePlaylistDetailsResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            thumbnail_url=playlist.thumbnail_url,
            video_count=total,
            videos=videos_envelope,
        )
