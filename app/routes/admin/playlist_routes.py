from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, status

from app.dependencies import get_current_user
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
from app.services.playlist_service import PlaylistService

router = APIRouter(prefix="/api/v1/admin/playlists", tags=["Admin Playlists"])
playlist_service = PlaylistService()

@router.post("", response_model=PlaylistCreateResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(payload: PlaylistCreateRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/playlists — Creates a new playlist container and links initial video IDs.
    """
    return playlist_service.create_playlist(current_user["user_id"], payload)

@router.get("", response_model=PaginatedResponse[PlaylistListItemResponse], status_code=status.HTTP_200_OK)
def list_playlists(
    search: Optional[str] = Query(None, description="Search playlist names by substring"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, oldest, title"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/admin/playlists — Retrieves a paginated list of lightweight playlist summaries.
    """
    return playlist_service.list_user_playlists(
        user_id=current_user["user_id"],
        search=search,
        sort=sort,
        page=page,
        limit=limit
    )

@router.get("/{playlist_id}", response_model=PlaylistDetailsResponse, status_code=status.HTTP_200_OK)
def get_playlist_details(playlist_id: int, current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/admin/playlists/{playlist_id} — Retrieves full metadata for a single playlist container.
    """
    return playlist_service.get_playlist_details(current_user["user_id"], playlist_id)

@router.put("/{playlist_id}", response_model=PlaylistUpdateResponse, status_code=status.HTTP_200_OK)
def update_playlist(playlist_id: int, payload: PlaylistUpdateRequest, current_user: dict = Depends(get_current_user)):
    """
    PUT /api/v1/admin/playlists/{playlist_id} — Updates playlist textual metadata (name, description).
    """
    return playlist_service.update_playlist_metadata(current_user["user_id"], playlist_id, payload)

@router.post("/{playlist_id}/thumbnail/upload", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def upload_playlist_banner(playlist_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/playlists/{playlist_id}/thumbnail/upload — Uploads a playlist cover banner image via server proxy.
    """
    return playlist_service.upload_playlist_banner(current_user["user_id"], playlist_id, file=file)

@router.delete("/{playlist_id}", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def delete_playlist(playlist_id: int, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/admin/playlists/{playlist_id} — Deletes a playlist container from DB.
    """
    return playlist_service.delete_playlist(current_user["user_id"], playlist_id)

@router.get("/{playlist_id}/videos", response_model=PaginatedResponse[PlaylistItemVideoResponse], status_code=status.HTTP_200_OK)
def get_playlist_videos(
    playlist_id: int,
    search: Optional[str] = Query(None, description="Search attached videos by title substring"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/admin/playlists/{playlist_id}/videos — Retrieves a paginated list of videos attached inside a playlist.
    """
    return playlist_service.get_playlist_videos(
        user_id=current_user["user_id"],
        playlist_id=playlist_id,
        search=search,
        page=page,
        limit=limit
    )

@router.post("/{playlist_id}/videos", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def add_videos_to_playlist(playlist_id: int, payload: PlaylistAddVideosRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/playlists/{playlist_id}/videos — Adds an array of video IDs to a playlist.
    """
    return playlist_service.add_videos_to_playlist(current_user["user_id"], playlist_id, payload)

@router.delete("/{playlist_id}/videos/{video_id}", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def remove_single_video_from_playlist(playlist_id: int, video_id: int, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/admin/playlists/{playlist_id}/videos/{video_id} — Removes a single video from a playlist.
    """
    return playlist_service.remove_single_video_from_playlist(current_user["user_id"], playlist_id, video_id)

@router.delete("/{playlist_id}/videos", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def bulk_remove_videos_from_playlist(playlist_id: int, payload: PlaylistBulkRemoveVideosRequest, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/admin/playlists/{playlist_id}/videos — Bulk removes multiple videos from a playlist.
    """
    return playlist_service.bulk_remove_videos_from_playlist(current_user["user_id"], playlist_id, payload)

@router.put("/{playlist_id}/videos/reorder", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def reorder_playlist_videos(playlist_id: int, payload: PlaylistReorderVideosRequest, current_user: dict = Depends(get_current_user)):
    """
    PUT /api/v1/admin/playlists/{playlist_id}/videos/reorder — Persists updated sequence positions of videos inside a playlist.
    """
    return playlist_service.reorder_playlist_videos(current_user["user_id"], playlist_id, payload)

@router.get("/{playlist_id}/available_videos", response_model=PaginatedResponse[PlaylistAvailableVideoResponse], status_code=status.HTTP_200_OK)
def get_available_videos_for_playlist(
    playlist_id: int,
    search: Optional[str] = Query(None, description="Search available videos by title substring"),
    category: Optional[str] = Query(None, description="Filter available videos by category slug"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, oldest, views, title"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/admin/playlists/{playlist_id}/available_videos — Fetches paginated, filterable available videos for playlist picker UI.
    """
    return playlist_service.get_available_videos(
        user_id=current_user["user_id"],
        playlist_id=playlist_id,
        search=search,
        category=category,
        sort=sort,
        page=page,
        limit=limit
    )
