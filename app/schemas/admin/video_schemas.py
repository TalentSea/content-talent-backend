from datetime import datetime

from pydantic import BaseModel, Field


class VideoInitiateRequest(BaseModel):
    """Request payload for initiating a video upload session."""

    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = []
    status: str | None = "draft"


class VideoInitiateResponse(BaseModel):
    """Response payload returned after video upload initiation."""

    id: int
    bunny_video_id: str
    bunny_library_id: str
    status: str
    signature: str
    expiration_time: int


class DownloadUrlItem(BaseModel):
    """Canonical DTO for individual resolution MP4 presigned download link."""

    resolution: str
    label: str
    url: str


class VideoListItemResponse(BaseModel):
    """Canonical DTO for item summary in paginated list matching spec doc API 3."""

    id: int
    title: str
    category: str | None = None
    status: str
    encode_progress: int
    is_playable: bool
    views: int = 0
    likes: int = 0
    duration: str | None = None
    main_thumbnail_url: str | None = None
    published_at: datetime | None = None
    scheduled_at: datetime | None = None
    created_at: datetime | None = None


class VideoResponse(BaseModel):
    """Canonical DTO for single video details matching spec doc API 4."""

    id: int
    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = []
    status: str
    encode_progress: int
    is_playable: bool
    views: int = 0
    likes: int = 0
    duration: str | None = None
    playback_url: str | None = None
    main_thumbnail_url: str | None = None
    alt_thumbnail_urls: list[str] = []
    captions_data: list[dict] = []
    download_urls: list[DownloadUrlItem] = []
    published_at: datetime | None = None
    scheduled_at: datetime | None = None
    created_at: datetime | None = None


class VideoUpdateRequest(BaseModel):
    """Request payload for updating video textual metadata matching spec doc API 5."""

    title: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class VideoUpdateResponse(BaseModel):
    """Pure text-only response for PATCH /api/v1/admin/videos/{video_id} matching spec doc API 5."""

    id: int
    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = []
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
    published_at: datetime | None = None


class VideoScheduleRequest(BaseModel):
    """Request payload for scheduling video publication matching spec doc API 11."""

    date: str = Field(..., description="Target publication date in YYYY-MM-DD format")
    time: str = Field(..., description="Target publication time in HH:MM format")


class VideoScheduleResponse(BaseModel):
    """Response payload returned when a video is scheduled matching spec doc API 11."""

    id: int
    status: str = "scheduled"
    scheduled_at: datetime | None = None


class BulkDeleteVideosRequest(BaseModel):
    """Request payload for bulk deleting multiple video assets matching spec doc API 12."""

    video_ids: list[int]


class BunnyWebhookPayload(BaseModel):
    """Payload envelope sent by Bunny Stream webhook events matching spec doc API 2."""

    VideoLibraryId: int
    VideoGuid: str
    Status: int
