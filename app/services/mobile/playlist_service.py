import logging

from fastapi import HTTPException, status

from app.repositories.mobile.playlist_repository import MobilePlaylistRepository
from app.schemas.mobile.playlist_schemas import (
    MobilePlaylistDetailsResponse,
    MobilePlaylistListItemResponse,
    MobilePlaylistListResponse,
    MobilePlaylistSaveResponse,
    MobilePlaylistVideoItemResponse,
    MobilePlaylistVideosResponse,
    MobileSavedPlaylistListItemResponse,
    MobileSavedPlaylistListResponse,
)
from app.schemas.mobile.video_schemas import WatchProgressResponse

logger = logging.getLogger(__name__)


class MobilePlaylistService:
    """
    Business logic layer for Mobile Subscriber Playlist Feed & Video Streaming operations.
    """

    def __init__(self):
        self.repo = MobilePlaylistRepository()

    def list_public_playlists(
        self,
        tenant_id: int | None = None,
        subscriber_id: int | None = None,
        search: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> MobilePlaylistListResponse:
        """
        Retrieves paginated public creator playlists feed with personalized is_saved bookmark state matching spec API 1.
        """
        results, total = self.repo.list_public_playlists(
            tenant_id=tenant_id,
            subscriber_id=subscriber_id,
            search=search,
            sort=sort,
            page=page,
            limit=limit,
        )

        items = [
            MobilePlaylistListItemResponse(
                id=playlist.id,
                name=playlist.name,
                thumbnail_url=playlist.thumbnail_url,
                video_count=video_count,
                is_saved=is_saved,
                created_at=playlist.created_at,
            )
            for playlist, video_count, is_saved in results
        ]

        return MobilePlaylistListResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def get_playlist_details(
        self,
        playlist_id: int,
        subscriber_id: int | None = None,
        tenant_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> MobilePlaylistDetailsResponse:
        """
        Retrieves single public playlist header alongside paginated video items matching spec API 2.
        """
        playlist = self.repo.get_public_playlist_by_id(
            playlist_id, tenant_id=tenant_id
        )
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        video_items, total = self.repo.get_playlist_videos(
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

        videos_envelope = MobilePlaylistVideosResponse.create(
            items=formatted_video_items, total=total, page=page, limit=limit
        )

        is_saved = False
        if subscriber_id:
            is_saved = self.repo.is_playlist_saved(playlist.id, subscriber_id)

        return MobilePlaylistDetailsResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            thumbnail_url=playlist.thumbnail_url,
            video_count=total,
            is_saved=is_saved,
            videos=videos_envelope,
        )

    def toggle_playlist_save(
        self,
        playlist_id: int,
        subscriber_id: int | None,
        tenant_id: int | None = None,
    ) -> MobilePlaylistSaveResponse:
        """
        Toggles save/bookmark state on a public playlist for the authenticated subscriber.
        """
        if not subscriber_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Subscriber authentication required to save playlist",
            )

        playlist = self.repo.get_public_playlist_by_id(
            playlist_id, tenant_id=tenant_id
        )
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        is_saved = self.repo.toggle_playlist_save(playlist_id, subscriber_id)
        return MobilePlaylistSaveResponse(is_saved=is_saved)

    def list_subscriber_saved_playlists(
        self,
        subscriber_id: int | None,
        tenant_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> MobileSavedPlaylistListResponse:
        """
        Retrieves paginated public playlists saved by subscriber matching spec.
        """
        if not subscriber_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Subscriber authentication required to view saved playlists",
            )

        results, total = self.repo.list_subscriber_saved_playlists(
            subscriber_id=subscriber_id,
            tenant_id=tenant_id,
            page=page,
            limit=limit,
        )

        items = [
            MobileSavedPlaylistListItemResponse(
                id=playlist.id,
                name=playlist.name,
                thumbnail_url=playlist.thumbnail_url,
                video_count=video_count,
                created_at=playlist.created_at,
            )
            for playlist, video_count in results
        ]

        return MobileSavedPlaylistListResponse.create(
            items=items, total=total, page=page, limit=limit
        )

