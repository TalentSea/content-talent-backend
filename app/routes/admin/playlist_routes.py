from fastapi import APIRouter, Query, status

from app.dependencies import CurrentAdmin, FormFile
from app.schemas.shared.common_schemas import ActionSuccessResponse, PaginatedResponse
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
from app.services.admin.playlist_service import PlaylistService

router = APIRouter(prefix="/api/v1/admin/playlists", tags=["Admin Playlists"])
playlist_service = PlaylistService()


@router.post(
    "", response_model=PlaylistCreateResponse, status_code=status.HTTP_201_CREATED
)
def create_playlist(payload: PlaylistCreateRequest, current_user: CurrentAdmin):
    """
    POST /api/v1/admin/playlists — Creates a new playlist container.
    """
    return playlist_service.create_playlist(current_user["user_id"], payload)


@router.get(
    "",
    response_model=PaginatedResponse[PlaylistListItemResponse],
    status_code=status.HTTP_200_OK,
)
def list_playlists(
    current_user: CurrentAdmin,
    search: str | None = Query(None, description="Search playlists by name substring"),
    sort: str | None = Query(
        "newest", description="Sort order: newest, oldest, title, videoCount"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/admin/playlists — Retrieves a paginated list of creator playlists.
    """
    return playlist_service.list_user_playlists(
        user_id=current_user["user_id"],
        search=search,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.put(
    "/{playlist_id}",
    response_model=PlaylistUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_playlist(
    playlist_id: int, payload: PlaylistUpdateRequest, current_user: CurrentAdmin
):
    """
    PUT /api/v1/admin/playlists/{playlist_id} — Updates playlist textual metadata (name, description).
    """
    return playlist_service.update_playlist_metadata(
        current_user["user_id"], playlist_id, payload
    )


@router.post(
    "/{playlist_id}/thumbnail/upload",
    response_model=PlaylistThumbnailUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_playlist_banner(
    playlist_id: int, current_user: CurrentAdmin, file: FormFile
):
    """
    POST /api/v1/admin/playlists/{playlist_id}/thumbnail/upload — Uploads a playlist cover banner image via server proxy.
    """
    return playlist_service.upload_playlist_banner(
        current_user["user_id"], playlist_id, file=file
    )


@router.delete(
    "/{playlist_id}",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def delete_playlist(playlist_id: int, current_user: CurrentAdmin):
    """
    DELETE /api/v1/admin/playlists/{playlist_id} — Deletes a playlist container from DB.
    """
    return playlist_service.delete_playlist(current_user["user_id"], playlist_id)


@router.get(
    "/{playlist_id}/videos",
    response_model=PaginatedResponse[PlaylistItemVideoResponse],
    status_code=status.HTTP_200_OK,
)
def get_playlist_videos(
    playlist_id: int,
    current_user: CurrentAdmin,
    search: str | None = Query(
        None, description="Search attached videos by title substring"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/admin/playlists/{playlist_id}/videos — Retrieves a paginated list of videos attached inside a playlist.
    """
    return playlist_service.get_playlist_videos(
        user_id=current_user["user_id"],
        playlist_id=playlist_id,
        search=search,
        page=page,
        limit=limit,
    )


@router.post(
    "/{playlist_id}/videos",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def add_videos_to_playlist(
    playlist_id: int, payload: PlaylistAddVideosRequest, current_user: CurrentAdmin
):
    """
    POST /api/v1/admin/playlists/{playlist_id}/videos — Adds an array of video IDs to a playlist.
    """
    return playlist_service.add_videos_to_playlist(
        current_user["user_id"], playlist_id, payload
    )


@router.delete(
    "/{playlist_id}/videos/{video_id}",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def remove_single_video_from_playlist(
    playlist_id: int, video_id: int, current_user: CurrentAdmin
):
    """
    DELETE /api/v1/admin/playlists/{playlist_id}/videos/{video_id} — Removes a single video from a playlist.
    """
    return playlist_service.remove_single_video_from_playlist(
        current_user["user_id"], playlist_id, video_id
    )


@router.delete(
    "/{playlist_id}/videos",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_remove_videos_from_playlist(
    playlist_id: int,
    payload: PlaylistBulkRemoveVideosRequest,
    current_user: CurrentAdmin,
):
    """
    DELETE /api/v1/admin/playlists/{playlist_id}/videos — Bulk removes multiple videos from a playlist.
    """
    return playlist_service.bulk_remove_videos_from_playlist(
        current_user["user_id"], playlist_id, payload
    )


@router.put(
    "/{playlist_id}/videos/reorder",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def reorder_playlist_videos(
    playlist_id: int, payload: PlaylistReorderVideosRequest, current_user: CurrentAdmin
):
    """
    PUT /api/v1/admin/playlists/{playlist_id}/videos/reorder — Persists updated sequence positions of videos inside a playlist.
    """
    return playlist_service.reorder_playlist_videos(
        current_user["user_id"], playlist_id, payload
    )


@router.get(
    "/{playlist_id}/available_videos",
    response_model=PaginatedResponse[PlaylistAvailableVideoResponse],
    status_code=status.HTTP_200_OK,
)
def get_available_videos_for_playlist(
    playlist_id: int,
    current_user: CurrentAdmin,
    search: str | None = Query(
        None, description="Search available videos by title substring"
    ),
    category: str | None = Query(
        None, description="Filter available videos by category slug"
    ),
    sort: str | None = Query(
        "newest", description="Sort order: newest, oldest, views, title"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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
        limit=limit,
    )
