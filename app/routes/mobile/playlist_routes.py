from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_subscriber
from app.schemas.mobile_playlist_schemas import (
    MobilePlaylistListResponse,
    MobilePlaylistDetailsResponse
)
from app.services.mobile_playlist_service import MobilePlaylistService

router = APIRouter(prefix="/api/v1/mobile/playlists", tags=["Mobile Playlists Feed"])
playlist_service = MobilePlaylistService()

@router.get("", response_model=MobilePlaylistListResponse, status_code=status.HTTP_200_OK)
def list_public_playlists(
    search: Optional[str] = Query(None, description="Filter playlists by name substring"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, oldest, title"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_subscriber: dict = Depends(get_current_subscriber)
):
    """
    GET /api/v1/mobile/playlists — Retrieves paginated public creator playlists feed matching spec API 1.
    Requires subscriber/guest Bearer token.
    """
    return playlist_service.list_public_playlists(
        search=search,
        sort=sort,
        page=page,
        limit=limit
    )

@router.get("/{playlist_id}", response_model=MobilePlaylistDetailsResponse, status_code=status.HTTP_200_OK)
def get_playlist_details(
    playlist_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_subscriber: dict = Depends(get_current_subscriber)
):
    """
    GET /api/v1/mobile/playlists/{playlist_id} — Retrieves playlist header details & paginated video items matching spec API 2.
    Populates personalized watch progress, like states, and saves overlay for authenticated subscribers.
    """
    return playlist_service.get_playlist_details(
        playlist_id=playlist_id,
        subscriber_id=current_subscriber["user_id"],
        page=page,
        limit=limit
    )
