from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PlaylistCreateRequest(BaseModel):
    """Request payload for creating a new playlist matching spec doc API 1."""
    name: str
    description: Optional[str] = None
    video_ids: Optional[List[int]] = []

class PlaylistCreateResponse(BaseModel):
    """Response payload returned when a playlist is created matching spec doc API 1."""
    id: int
    name: str
    description: Optional[str] = None
    video_count: int = 0
    created_at: Optional[datetime] = None

class PlaylistListItemResponse(BaseModel):
    """Lightweight DTO for listing creator playlists matching spec doc API 2."""
    id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PlaylistDetailsResponse(BaseModel):
    """Detailed DTO for single playlist views matching spec doc API 3."""
    id: int
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PlaylistUpdateRequest(BaseModel):
    """Request payload for updating playlist textual metadata matching spec doc API 4."""
    name: Optional[str] = None
    description: Optional[str] = None

class PlaylistUpdateResponse(BaseModel):
    """Text-only response payload returned when a playlist is updated matching spec doc API 4."""
    id: int
    name: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


class PlaylistItemVideoResponse(BaseModel):
    """Canonical DTO representation for videos inside a playlist matching spec doc API 7."""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    is_playable: bool
    views: int = 0
    duration: Optional[str] = None
    main_thumbnail_url: Optional[str] = None
    order: int = 0
    added_at: Optional[datetime] = None

class PlaylistAddVideosRequest(BaseModel):
    """Request payload for adding videos to a playlist matching spec doc API 8."""
    video_ids: List[int]

class PlaylistBulkRemoveVideosRequest(BaseModel):
    """Request payload for bulk removing videos from a playlist matching spec doc API 10."""
    video_ids: List[int]

class VideoOrderSchema(BaseModel):
    """DTO representing target sequence position for a video."""
    video_id: int
    order: int

class PlaylistReorderVideosRequest(BaseModel):
    """Request payload for reordering videos inside a playlist matching spec doc API 12."""
    video_orders: List[VideoOrderSchema]

class PlaylistAvailableVideoResponse(BaseModel):
    """DTO for unattached videos in the playlist picker modal matching spec doc API 11."""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    is_playable: bool
    views: int = 0
    duration: Optional[str] = None
    main_thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
