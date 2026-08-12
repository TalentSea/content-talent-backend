from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.common_schemas import PaginatedResponse
from app.schemas.mobile_video_schemas import WatchProgressResponse

class MobilePlaylistListItemResponse(BaseModel):
    """Canonical DTO for public playlist cards in mobile discovery feed matching spec API 1."""
    id: int
    name: str
    thumbnail_url: Optional[str] = None
    video_count: int = 0
    created_at: Optional[datetime] = None

class MobilePlaylistListResponse(PaginatedResponse[MobilePlaylistListItemResponse]):
    """Paginated list envelope for public mobile playlists matching spec API 1."""
    pass

class MobilePlaylistVideoItemResponse(BaseModel):
    """Canonical DTO for ordered videos inside a playlist with subscriber watch state matching spec API 2."""
    id: int
    title: str
    category: Optional[str] = None
    duration: Optional[str] = None
    main_thumbnail_url: Optional[str] = None
    views: int = 0
    likes: int = 0
    is_liked: bool = False
    is_saved: bool = False
    watch_progress: Optional[WatchProgressResponse] = None
    order: int = 0
    created_at: Optional[datetime] = None

class MobilePlaylistVideosResponse(PaginatedResponse[MobilePlaylistVideoItemResponse]):
    """Paginated video items envelope inside playlist details matching spec API 2."""
    pass

class MobilePlaylistDetailsResponse(BaseModel):
    """Unified DTO for mobile playlist header and paginated video items matching spec API 2."""
    id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_count: int = 0
    videos: MobilePlaylistVideosResponse
