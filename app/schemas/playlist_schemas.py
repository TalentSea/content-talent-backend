from datetime import datetime

from pydantic import BaseModel


class PlaylistCreateRequest(BaseModel):
    """Request payload for creating a new playlist matching spec doc API 1."""

    name: str
    description: str | None = None
    video_ids: list[int] | None = []


class PlaylistCreateResponse(BaseModel):
    """Response payload returned when a playlist is created matching spec doc API 1."""

    id: int
    name: str
    description: str | None = None
    video_count: int = 0
    created_at: datetime | None = None


class PlaylistListItemResponse(BaseModel):
    """Lightweight DTO for listing creator playlists matching spec doc API 2."""

    id: int
    name: str
    description: str | None = None
    thumbnail_url: str | None = None
    video_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlaylistThumbnailUploadResponse(BaseModel):
    """Response payload returned when a playlist thumbnail image is uploaded matching spec doc API 5."""

    thumbnail_url: str


class PlaylistUpdateRequest(BaseModel):
    """Request payload for updating playlist textual metadata matching spec doc API 4."""

    name: str | None = None
    description: str | None = None


class PlaylistUpdateResponse(BaseModel):
    """Text-only response payload returned when a playlist is updated matching spec doc API 4."""

    id: int
    name: str
    description: str | None = None
    updated_at: datetime | None = None


class PlaylistItemVideoResponse(BaseModel):
    """Canonical DTO representation for videos inside a playlist matching spec doc API 7."""

    id: int
    title: str
    category: str | None = None
    status: str
    is_playable: bool
    views: int = 0
    likes: int = 0
    duration: str | None = None
    main_thumbnail_url: str | None = None
    order: int = 0
    added_at: datetime | None = None


class PlaylistAddVideosRequest(BaseModel):
    """Request payload for adding videos to a playlist matching spec doc API 8."""

    video_ids: list[int]


class PlaylistBulkRemoveVideosRequest(BaseModel):
    """Request payload for bulk removing videos from a playlist matching spec doc API 10."""

    video_ids: list[int]


class VideoOrderSchema(BaseModel):
    """DTO representing target sequence position for a video."""

    video_id: int
    order: int


class PlaylistReorderVideosRequest(BaseModel):
    """Request payload for reordering videos inside a playlist matching spec doc API 12."""

    video_orders: list[VideoOrderSchema]


class PlaylistAvailableVideoResponse(BaseModel):
    """DTO for unattached videos in the playlist picker modal matching spec doc API 11."""

    id: int
    title: str
    category: str | None = None
    status: str
    is_playable: bool
    views: int = 0
    likes: int = 0
    duration: str | None = None
    main_thumbnail_url: str | None = None
    created_at: datetime | None = None
