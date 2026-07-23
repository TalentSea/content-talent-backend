from typing import List, Optional
from pydantic import BaseModel

class PlaylistCreateRequest(BaseModel):
    """Request payload for creating a new playlist."""
    name: str
    description: Optional[str] = None
    video_ids: Optional[List[int]] = []

class PlaylistUpdateRequest(BaseModel):
    """Request payload for editing playlist details or video links."""
    name: Optional[str] = None
    description: Optional[str] = None
    video_ids: Optional[List[int]] = None

class PlaylistItemVideoResponse(BaseModel):
    """Canonical video DTO representation inside playlist responses."""
    id: int
    title: str
    description: Optional[str] = None
    bunny_video_id: str
    main_thumbnail_url: Optional[str] = None

class PlaylistSummaryResponse(BaseModel):
    """Lightweight DTO for listing playlists (GET /playlists)."""
    id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_count: int

class PlaylistResponse(BaseModel):
    """Detailed DTO for single playlist views (GET /playlists/{id})."""
    id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_count: int
    page: Optional[int] = 1
    limit: Optional[int] = 20
    total_pages: Optional[int] = 1
    videos: List[PlaylistItemVideoResponse] = []

class PlaylistCreateResponse(BaseModel):
    """Response payload returned when a playlist is created."""
    id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    image_upload_url: str
    video_count: int
    videos: List[PlaylistItemVideoResponse] = []

class PlaylistBannerUploadUrlResponse(BaseModel):
    """Response payload for requesting playlist banner upload URL."""
    thumbnail_url: str
    image_upload_url: str
