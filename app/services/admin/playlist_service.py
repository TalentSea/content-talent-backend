import logging
import time

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.models.video import Video, VideoLike
from app.repositories.admin.playlist_repository import PlaylistRepository
from app.schemas.admin.playlist_schemas import (
    PlaylistAddVideosRequest,
    PlaylistAvailableVideoResponse,
    PlaylistBulkRemoveVideosRequest,
    PlaylistCreateRequest,
    PlaylistCreateResponse,
    PlaylistItemVideoResponse,
    PlaylistListItemResponse,
    PlaylistReorderVideosRequest,
    PlaylistThumbnailUploadResponse,
    PlaylistUpdateRequest,
    PlaylistUpdateResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.utils.bunny_client import delete_bunny_storage_file
from app.utils.image_uploader import validate_and_upload_image

logger = logging.getLogger(__name__)


class PlaylistService:
    """
    Business logic layer for Admin Playlist operations (Peewee ORM).
    Scoping is enforced by Tenant.
    """

    def __init__(self):
        self.repo = PlaylistRepository()

    def _validate_no_shorts(self, tenant_id: int, video_ids: list[int] | None) -> None:
        """
        Validates that none of the provided video IDs are short videos.
        Raises HTTP 400 Bad Request if any short videos are detected.
        """
        if not video_ids:
            return

        shorts_exist = (
            Video.select()
            .where(
                (Video.id.in_(video_ids))
                & (Video.tenant == tenant_id)
                & (Video.video_type == "shorts")
            )
            .exists()
        )
        if shorts_exist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short videos cannot be added to playlists",
            )

    def create_playlist(
        self, tenant_id: int, payload: PlaylistCreateRequest, created_by: int | None = None
    ) -> PlaylistCreateResponse:
        """
        Creates a new playlist container and attaches initial video IDs in DB.
        """
        self._validate_no_shorts(tenant_id, payload.video_ids)

        playlist_data = payload.model_dump()
        playlist = self.repo.create_playlist(
            playlist_data, tenant_id=tenant_id, created_by=created_by
        )
        video_count = self.repo.get_playlist_video_count(playlist)

        return PlaylistCreateResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            video_count=video_count,
            created_at=playlist.created_at,
        )

    def list_user_playlists(
        self,
        tenant_id: int,
        search: str | None = None,
        sort: str | None = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[PlaylistListItemResponse]:
        """
        Retrieves a paginated, filterable list of playlists created under tenant_id.
        """
        playlists_with_counts, total = self.repo.get_all_playlists_by_user(
            tenant_id=tenant_id, search=search, sort=sort, page=page, limit=limit
        )

        items = [
            PlaylistListItemResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                thumbnail_url=p.thumbnail_url,
                video_count=v_count,
                saves_count=s_count,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p, v_count, s_count in playlists_with_counts
        ]

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def update_playlist_metadata(
        self, tenant_id: int, playlist_id: int, payload: PlaylistUpdateRequest
    ) -> PlaylistUpdateResponse:
        """
        Updates playlist textual metadata (name, description).
        """
        update_data = payload.model_dump(exclude_unset=True)
        playlist = self.repo.update_playlist(playlist_id, tenant_id, update_data)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        return PlaylistUpdateResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            updated_at=playlist.updated_at,
        )

    def upload_playlist_banner(
        self, tenant_id: int, playlist_id: int, file: UploadFile
    ) -> PlaylistThumbnailUploadResponse:
        """
        Uploads playlist banner image binary to Bunny Storage via centralized image uploader.
        """
        playlist = self.repo.get_playlist_by_id(playlist_id, tenant_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        settings = get_settings()
        timestamp = int(time.time())

        thumbnail_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/playlists/pl_{playlist_id}_{timestamp}",
            max_size_mb=settings.MAX_PLAYLIST_COVER_SIZE_MB,
            old_file_url=playlist.thumbnail_url,
            old_file_storage_folder="assets/playlists",
        )

        playlist.thumbnail_url = thumbnail_url
        playlist.save()

        return PlaylistThumbnailUploadResponse(thumbnail_url=thumbnail_url)

    def delete_playlist(self, tenant_id: int, playlist_id: int) -> ActionSuccessResponse:
        """
        Deletes a playlist record from DB and clears banner image from Bunny Storage.
        """
        playlist = self.repo.get_playlist_by_id(playlist_id, tenant_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        if playlist.thumbnail_url:
            try:
                filename = playlist.thumbnail_url.split("/")[-1]
                banner_path = f"assets/playlists/{filename}"
                delete_bunny_storage_file(banner_path)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to delete Bunny Storage banner for playlist %s: %s",
                    playlist_id,
                    e,
                )

        self.repo.delete_playlist(playlist_id, tenant_id)
        return ActionSuccessResponse(status="success")

    def get_playlist_videos(
        self,
        tenant_id: int,
        playlist_id: int,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[PlaylistItemVideoResponse]:
        """
        Retrieves a paginated list of attached videos inside a playlist with order and added_at metadata.
        """
        playlist, video_tuples, total = self.repo.get_playlist_videos(
            playlist_id=playlist_id,
            tenant_id=tenant_id,
            search=search,
            page=page,
            limit=limit,
        )
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        items = [
            PlaylistItemVideoResponse(
                id=v.id,
                title=v.title,
                category=v.category,
                status=v.status,
                is_playable=v.is_playable,
                views=v.views or 0,
                likes=VideoLike.select().where(VideoLike.video == v.id).count(),
                duration=v.duration,
                main_thumbnail_url=v.main_thumbnail_url,
                order=order_val,
                added_at=added_at_val,
            )
            for v, order_val, added_at_val in video_tuples
        ]

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def add_videos_to_playlist(
        self, tenant_id: int, playlist_id: int, payload: PlaylistAddVideosRequest
    ) -> ActionSuccessResponse:
        """
        Adds an array of video IDs to a playlist.
        """
        self._validate_no_shorts(tenant_id, payload.video_ids)

        playlist = self.repo.add_videos_to_playlist(
            playlist_id, tenant_id, payload.video_ids
        )
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        return ActionSuccessResponse(status="success")

    def remove_single_video_from_playlist(
        self, tenant_id: int, playlist_id: int, video_id: int
    ) -> ActionSuccessResponse:
        """
        Removes a single video from a playlist.
        """
        success = self.repo.remove_video_from_playlist(playlist_id, tenant_id, video_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} or video link not found",
            )

        return ActionSuccessResponse(status="success")

    def bulk_remove_videos_from_playlist(
        self, tenant_id: int, playlist_id: int, payload: PlaylistBulkRemoveVideosRequest
    ) -> ActionSuccessResponse:
        """
        Bulk removes an array of video IDs from a playlist.
        """
        success = self.repo.bulk_remove_videos_from_playlist(
            playlist_id, tenant_id, payload.video_ids
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        return ActionSuccessResponse(status="success")

    def reorder_playlist_videos(
        self, tenant_id: int, playlist_id: int, payload: PlaylistReorderVideosRequest
    ) -> ActionSuccessResponse:
        """
        Persists updated sequence positions (order) of videos attached to a playlist.
        """
        video_orders_data = [vo.model_dump() for vo in payload.video_orders]
        success = self.repo.reorder_playlist_videos(
            playlist_id, tenant_id, video_orders_data
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playlist {playlist_id} not found",
            )

        return ActionSuccessResponse(status="success")

    def get_available_videos(
        self,
        tenant_id: int,
        playlist_id: int,
        search: str | None = None,
        category: str | None = None,
        sort: str | None = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[PlaylistAvailableVideoResponse]:
        """
        Fetches a paginated, filterable list of tenant videos available to be added to the playlist.
        """
        results, total = self.repo.get_available_videos_for_playlist(
            playlist_id=playlist_id,
            tenant_id=tenant_id,
            search=search,
            category=category,
            sort=sort,
            page=page,
            limit=limit,
        )

        items = [
            PlaylistAvailableVideoResponse(
                id=v.id,
                title=v.title,
                category=v.category,
                status=v.status,
                is_playable=v.is_playable,
                views=v.views or 0,
                likes=likes_count or 0,
                duration=v.duration,
                main_thumbnail_url=v.main_thumbnail_url,
                created_at=v.created_at,
            )
            for v, likes_count in results
        ]

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )
