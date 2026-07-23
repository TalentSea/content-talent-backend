from fastapi import APIRouter, Depends, Query, status
from app.dependencies import get_current_user
from app.schemas.playlist_schemas import (
    PlaylistCreateRequest,
    PlaylistCreateResponse,
    PlaylistSummaryResponse,
    PlaylistResponse,
    PlaylistUpdateRequest,
    PlaylistBannerUploadUrlResponse,
    PlaylistItemVideoResponse
)
from app.schemas.common_schemas import PaginatedResponse

router = APIRouter(prefix="/api/v1/playlists", tags=["Playlists"])

@router.post("", response_model=PlaylistCreateResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(payload: PlaylistCreateRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/playlists — Creates a playlist and returns deterministic banner upload URL (playlist_{id}.jpg).
    """
    pass

@router.get("", response_model=PaginatedResponse[PlaylistSummaryResponse], status_code=status.HTTP_200_OK)
def list_playlists(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/playlists — Retrieves a paginated list of playlist summaries (video_count) created by authenticated user.
    """
    pass

@router.get("/{playlist_id}", response_model=PlaylistResponse, status_code=status.HTTP_200_OK)
def get_playlist_details(playlist_id: int, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/playlists/{playlist_id} — Retrieves single playlist details and paginated attached video items.
    """
    pass

@router.put("/{playlist_id}", response_model=PlaylistResponse, status_code=status.HTTP_200_OK)
def update_playlist(playlist_id: int, payload: PlaylistUpdateRequest, current_user: dict = Depends(get_current_user)):
    """
    PUT /api/v1/playlists/{playlist_id} — Updates playlist name, description, or attached video ID list.
    """
    pass

@router.post("/{playlist_id}/thumbnail/upload-url", response_model=PlaylistBannerUploadUrlResponse, status_code=status.HTTP_200_OK)
def request_banner_upload_url(playlist_id: int, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/playlists/{playlist_id}/thumbnail/upload-url — Generates Bunny Storage URL to overwrite playlist_{id}.jpg.
    """
    pass

@router.delete("/{playlist_id}", status_code=status.HTTP_200_OK)
def delete_playlist(playlist_id: int, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/playlists/{playlist_id} — Deletes playlist record from database.
    """
    pass

@router.get("/{playlist_id}/available_videos", response_model=PaginatedResponse[PlaylistItemVideoResponse], status_code=status.HTTP_200_OK)
def get_available_videos(playlist_id: int, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/playlists/{playlist_id}/available_videos — Fetches paginated creator videos NOT attached to this playlist.
    """
    pass
