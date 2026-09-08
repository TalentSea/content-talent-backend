from datetime import datetime

from pydantic import BaseModel

from app.schemas.mobile.video_schemas import WatchProgressResponse
from app.schemas.shared.common_schemas import PaginatedResponse


class MobilePlaylistListItemResponse(BaseModel):
    """Canonical DTO for public playlist cards in mobile discovery feed matching spec API 1."""

    id: int
    name: str
    thumbnail_url: str | None = None
    video_count: int = 0
    created_at: datetime | None = None


class MobilePlaylistListResponse(PaginatedResponse[MobilePlaylistListItemResponse]):
    """Paginated list envelope for public mobile playlists matching spec API 1."""


class MobilePlaylistVideoItemResponse(BaseModel):
    """Canonical DTO for ordered videos inside a playlist with subscriber watch state matching spec API 2."""

    id: int
    title: str
    category: str | None = None
    duration: str | None = None
    main_thumbnail_url: str | None = None
    views: int = 0
    likes: int = 0
    is_liked: bool = False
    is_saved: bool = False
    watch_progress: WatchProgressResponse | None = None
    order: int = 0
    created_at: datetime | None = None


class MobilePlaylistVideosResponse(PaginatedResponse[MobilePlaylistVideoItemResponse]):
    """Paginated video items envelope inside playlist details matching spec API 2."""


class MobilePlaylistDetailsResponse(BaseModel):
    """Unified DTO for mobile playlist header and paginated video items matching spec API 2."""

    id: int
    name: str
    description: str | None = None
    thumbnail_url: str | None = None
    video_count: int = 0
    videos: MobilePlaylistVideosResponse
