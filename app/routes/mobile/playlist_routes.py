from fastapi import APIRouter, Query, status

from app.dependencies import CurrentSubscriber
from app.schemas.mobile.playlist_schemas import (
    MobilePlaylistDetailsResponse,
    MobilePlaylistListResponse,
    MobilePlaylistSaveResponse,
    MobileSavedPlaylistListResponse,
)
from app.services.mobile.playlist_service import MobilePlaylistService

router = APIRouter(prefix="/api/v1/mobile/playlists", tags=["Mobile Playlists Feed"])
playlist_service = MobilePlaylistService()


@router.get(
    "", response_model=MobilePlaylistListResponse, status_code=status.HTTP_200_OK
)
def list_public_playlists(
    current_subscriber: CurrentSubscriber,
    search: str | None = Query(None, description="Filter playlists by name substring"),
    sort: str | None = Query("newest", description="Sort order: newest, oldest, title"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/mobile/playlists — Retrieves paginated public creator playlists feed with personalized is_saved bookmark state.
    Requires subscriber/guest Bearer token.
    """
    return playlist_service.list_public_playlists(
        creator_id=current_subscriber.get("creator_id"),
        subscriber_id=current_subscriber.get("user_id"),
        search=search,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.get(
    "/saved",
    response_model=MobileSavedPlaylistListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Subscriber Saved Playlists",
    description="Retrieves a paginated list of playlists bookmarked/saved by the authenticated subscriber.",
)
def list_subscriber_saved_playlists(
    current_subscriber: CurrentSubscriber,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/mobile/playlists/saved — Retrieves saved playlists feed.
    Must be declared before /{playlist_id} route to avoid path collision.
    """
    return playlist_service.list_subscriber_saved_playlists(
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
        page=page,
        limit=limit,
    )


@router.get(
    "/{playlist_id}",
    response_model=MobilePlaylistDetailsResponse,
    status_code=status.HTTP_200_OK,
)
def get_playlist_details(
    playlist_id: int,
    current_subscriber: CurrentSubscriber,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/mobile/playlists/{playlist_id} — Retrieves playlist header details & paginated video items matching spec API 2.
    Populates personalized watch progress, like states, and saves overlay for authenticated subscribers.
    """
    return playlist_service.get_playlist_details(
        playlist_id=playlist_id,
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
        page=page,
        limit=limit,
    )


@router.post(
    "/{playlist_id}/save",
    response_model=MobilePlaylistSaveResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Subscriber Playlist Bookmark",
    description="Toggles bookmark/save state (save / unsave) on a public playlist for an authenticated subscriber.",
)
def toggle_playlist_save(
    playlist_id: int,
    current_subscriber: CurrentSubscriber,
):
    """
    POST /api/v1/mobile/playlists/{playlist_id}/save — Toggles saved/bookmarked state.
    """
    return playlist_service.toggle_playlist_save(
        playlist_id=playlist_id,
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
    )
