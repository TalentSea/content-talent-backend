from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common_schemas import ActionSuccessResponse, PaginatedResponse

class VideoInitiateRequest(BaseModel):
    """Request payload for initiating a video upload session."""
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    status: Optional[str] = "draft"

class VideoInitiateResponse(BaseModel):
    """Response payload returned after video upload initiation."""
    id: int
    bunny_video_id: str
    bunny_library_id: str
    status: str
    signature: str
    expiration_time: int

class VideoListItemResponse(BaseModel):
    """Lightweight DTO for video items in paginated list response matching spec doc API 3."""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    status: str
    encode_progress: int
    is_playable: bool
    views: int = 0
    duration: Optional[str] = None
    main_thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class VideoResponse(BaseModel):
    """Canonical DTO for single video details matching spec doc API 4."""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    status: str
    encode_progress: int
    is_playable: bool
    views: int = 0
    duration: Optional[str] = None
    playback_url: Optional[str] = None
    main_thumbnail_url: Optional[str] = None
    alt_thumbnail_urls: List[str] = []
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class VideoUpdateRequest(BaseModel):
    """Request payload for updating video textual metadata matching spec doc API 5."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class VideoUpdateResponse(BaseModel):
    """Pure text-only response for PATCH /api/v1/admin/videos/{video_id} matching spec doc API 5."""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    status: str

class SelectMainThumbnailRequest(BaseModel):
    """Request payload for selecting a new main cover thumbnail matching spec doc API 7."""
    selected_main_thumbnail: str

class DeleteThumbnailRequest(BaseModel):
    """Request payload for deleting an alternative backup thumbnail matching spec doc API 8."""
    thumbnail_url: str

class VideoPublishResponse(BaseModel):
    """Response payload returned when a video is published immediately matching spec doc API 10."""
    id: int
    status: str = "published"
    published_at: Optional[datetime] = None

class VideoScheduleRequest(BaseModel):
    """Request payload for scheduling video publication matching spec doc API 11."""
    date: str = Field(..., description="Target publication date in YYYY-MM-DD format")
    time: str = Field(..., description="Target publication time in HH:MM format")
    timezone: str = Field("UTC", description="Target timezone string, e.g. America/Los_Angeles")

class VideoScheduleResponse(BaseModel):
    """Response payload returned when a video is scheduled matching spec doc API 11."""
    id: int
    status: str = "scheduled"
    scheduled_at: Optional[datetime] = None

class BulkDeleteVideosRequest(BaseModel):
    """Request payload for bulk deleting multiple video assets matching spec doc API 12."""
    video_ids: List[int]

class BunnyWebhookPayload(BaseModel):
    """Payload envelope sent by Bunny Stream webhook events matching spec doc API 2."""
    VideoLibraryId: int
    VideoGuid: str
    Status: int
