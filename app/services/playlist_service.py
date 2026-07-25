import logging
import math
from typing import Optional, List
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.playlist_repository import PlaylistRepository
from app.schemas.playlist_schemas import (
    PlaylistCreateRequest,
    PlaylistCreateResponse,
    PlaylistListItemResponse,
    PlaylistDetailsResponse,
    PlaylistUpdateRequest,
    PlaylistUpdateResponse,
    PlaylistItemVideoResponse,
    PlaylistAddVideosRequest,
    PlaylistBulkRemoveVideosRequest,
    PlaylistReorderVideosRequest,
    PlaylistAvailableVideoResponse
)
from app.schemas.common_schemas import PaginatedResponse, ActionSuccessResponse
from app.utils.bunny_client import (
    upload_bunny_storage_file,
    delete_bunny_storage_file
)

logger = logging.getLogger(__name__)

class PlaylistService:
    """
    Business logic layer for Admin Playlist operations (Peewee ORM).
    """

    def __init__(self):
        self.repo = PlaylistRepository()

    def create_playlist(self, user_id: int, payload: PlaylistCreateRequest) -> PlaylistCreateResponse:
        """
        Creates a new playlist container and attaches initial video IDs in DB.
        """
        playlist_data = payload.model_dump()
        playlist = self.repo.create_playlist(playlist_data, user_id)
        video_count = self.repo.get_playlist_video_count(playlist)

        return PlaylistCreateResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            video_count=video_count,
            created_at=playlist.created_at
        )

    def list_user_playlists(
        self,
        user_id: int,
        search: Optional[str] = None,
        sort: Optional[str] = "newest",
        page: int = 1,
        limit: int = 20
    ) -> PaginatedResponse[PlaylistListItemResponse]:
        """
        Retrieves a paginated, filterable list of playlists created by user_id matching spec doc API 2.
        """
        playlists_with_counts, total = self.repo.get_all_playlists_by_user(
            user_id=user_id,
            search=search,
            sort=sort,
            page=page,
            limit=limit
        )

        items = [
            PlaylistListItemResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                thumbnail_url=p.thumbnail_url,
                video_count=v_count,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p, v_count in playlists_with_counts
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items
        )

    def get_playlist_details(self, user_id: int, playlist_id: int) -> PlaylistDetailsResponse:
        """
        Retrieves detailed metadata for a single playlist matching spec doc API 3.
        """
        playlist = self.repo.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        video_count = self.repo.get_playlist_video_count(playlist)

        return PlaylistDetailsResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            thumbnail_url=playlist.thumbnail_url,
            video_count=video_count,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at
        )

    def update_playlist_metadata(self, user_id: int, playlist_id: int, payload: PlaylistUpdateRequest) -> PlaylistUpdateResponse:
        """
        Updates playlist textual metadata (name, description) matching spec doc API 4.
        """
        update_data = payload.model_dump(exclude_unset=True)
        playlist = self.repo.update_playlist(playlist_id, user_id, update_data)
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        return PlaylistUpdateResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            updated_at=playlist.updated_at
        )

    def upload_playlist_banner(self, user_id: int, playlist_id: int, file: UploadFile) -> ActionSuccessResponse:
        """
        Uploads playlist banner image binary to Bunny Storage (assets/playlists/playlist_{id}.jpg) via server proxy.
        """
        playlist = self.repo.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        allowed_mime_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        content_type = (file.content_type or "").lower()
        if content_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{file.content_type}'. Only JPEG, PNG, and WebP images are allowed."
            )

        file_bytes = file.file.read()
        settings = get_settings()
        pull_zone = settings.BUNNY_PULL_ZONE_URL.rstrip("/")

        ext = "png" if "png" in content_type else ("webp" if "webp" in content_type else "jpg")
        banner_path = f"assets/playlists/playlist_{playlist_id}.{ext}"
        thumbnail_url = f"{pull_zone}/{banner_path}"

        upload_bunny_storage_file(banner_path, file_bytes, content_type)

        playlist.thumbnail_url = thumbnail_url
        playlist.save()

        return ActionSuccessResponse(status="success")

    def delete_playlist(self, user_id: int, playlist_id: int) -> ActionSuccessResponse:
        """
        Deletes a playlist record from DB and clears banner image from Bunny Storage.
        """
        playlist = self.repo.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        if playlist.thumbnail_url:
            try:
                filename = playlist.thumbnail_url.split('/')[-1]
                banner_path = f"assets/playlists/{filename}"
                delete_bunny_storage_file(banner_path)
            except Exception as e:
                logger.warning(f"Failed to delete Bunny Storage banner for playlist {playlist_id}: {str(e)}")

        self.repo.delete_playlist(playlist_id, user_id)
        return ActionSuccessResponse(status="success")

    def get_playlist_videos(
        self,
        user_id: int,
        playlist_id: int,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> PaginatedResponse[PlaylistItemVideoResponse]:
        """
        Retrieves a paginated list of attached videos inside a playlist with order and added_at metadata matching spec doc API 7.
        """
        playlist, video_tuples, total = self.repo.get_playlist_videos(
            playlist_id=playlist_id,
            user_id=user_id,
            search=search,
            page=page,
            limit=limit
        )
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        items = [
            PlaylistItemVideoResponse(
                id=v.id,
                title=v.title,
                description=v.description,
                category=v.category,
                status=v.status,
                is_playable=v.is_playable,
                views=v.views or 0,
                duration=v.duration,
                main_thumbnail_url=v.main_thumbnail_url,
                order=order_val,
                added_at=added_at_val
            )
            for v, order_val, added_at_val in video_tuples
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items
        )

    def add_videos_to_playlist(self, user_id: int, playlist_id: int, payload: PlaylistAddVideosRequest) -> ActionSuccessResponse:
        """
        Adds an array of video IDs to a playlist matching spec doc API 8.
        """
        playlist = self.repo.add_videos_to_playlist(playlist_id, user_id, payload.video_ids)
        if not playlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        return ActionSuccessResponse(status="success")

    def remove_single_video_from_playlist(self, user_id: int, playlist_id: int, video_id: int) -> ActionSuccessResponse:
        """
        Removes a single video from a playlist matching spec doc API 9.
        """
        success = self.repo.remove_video_from_playlist(playlist_id, user_id, video_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} or video link not found")

        return ActionSuccessResponse(status="success")

    def bulk_remove_videos_from_playlist(self, user_id: int, playlist_id: int, payload: PlaylistBulkRemoveVideosRequest) -> ActionSuccessResponse:
        """
        Bulk removes an array of video IDs from a playlist matching spec doc API 10.
        """
        success = self.repo.bulk_remove_videos_from_playlist(playlist_id, user_id, payload.video_ids)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        return ActionSuccessResponse(status="success")

    def reorder_playlist_videos(self, user_id: int, playlist_id: int, payload: PlaylistReorderVideosRequest) -> ActionSuccessResponse:
        """
        Persists updated sequence positions (order) of videos attached to a playlist matching spec doc API 12.
        """
        video_orders_data = [vo.model_dump() for vo in payload.video_orders]
        success = self.repo.reorder_playlist_videos(playlist_id, user_id, video_orders_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playlist {playlist_id} not found")

        return ActionSuccessResponse(status="success")

    def get_available_videos(
        self,
        user_id: int,
        playlist_id: int,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort: Optional[str] = "newest",
        page: int = 1,
        limit: int = 20
    ) -> PaginatedResponse[PlaylistAvailableVideoResponse]:
        """
        Fetches a paginated, filterable list of creator videos available to be added to the playlist matching spec doc API 11.
        """
        videos, total = self.repo.get_available_videos_for_playlist(
            playlist_id=playlist_id,
            user_id=user_id,
            search=search,
            category=category,
            sort=sort,
            page=page,
            limit=limit
        )

        items = [
            PlaylistAvailableVideoResponse(
                id=v.id,
                title=v.title,
                description=v.description,
                category=v.category,
                status=v.status,
                is_playable=v.is_playable,
                views=v.views or 0,
                duration=v.duration,
                main_thumbnail_url=v.main_thumbnail_url,
                created_at=v.created_at
            )
            for v in videos
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items
        )
