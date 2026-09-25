from datetime import datetime

from pydantic import BaseModel, Field


class MobileVideoListItemResponse(BaseModel):
    """
    Lightweight DTO for mobile video catalog feed & search results.
    """

    id: int
    title: str
    thumbnail_url: str | None = None
    duration: int = 0
    views_count: int = 0
    category: str | None = None
    video_type: str = "standard"
    last_position_seconds: int | None = None
    progress_percentage: float | None = None
    published_at: datetime | None = None


class MobileVideoCaptionResponse(BaseModel):
    """
    Subtitle / Closed Caption track DTO.
    """

    language: str
    srclang: str
    url: str


class MobileVideoDownloadUrlResponse(BaseModel):
    """
    Offline MP4 download link DTO.
    """

    resolution: str
    url: str


class MobileVideoDetailResponse(BaseModel):
    """
    Detailed video DTO for mobile video player screen.
    Includes presigned HLS streaming URL, MP4 download URLs, captions, and engagement state.
    """

    id: int
    title: str
    description: str | None = None
    category: str | None = None
    video_type: str = "standard"
    tags: list[str] = Field(default_factory=list)
    duration: int = 0
    views_count: int = 0
    likes_count: int = 0
    is_liked: bool = False
    is_saved: bool = False
    last_position_seconds: int = 0
    progress_percentage: float = 0.0
    thumbnail_url: str | None = None
    hls_stream_url: str | None = None
    ad_tag_url: str | None = None
    download_urls: list[MobileVideoDownloadUrlResponse] | None = None
    captions: list[MobileVideoCaptionResponse] | None = None
    published_at: datetime | None = None


class MobileViewCountResponse(BaseModel):
    """
    Response schema for view count increment API.
    """

    status: str = "success"
    views_count: int


class MobileVideoLikeResponse(BaseModel):
    """
    Response schema for toggle subscriber video like API.
    """

    is_liked: bool
    likes_count: int


class MobileVideoSaveResponse(BaseModel):
    """
    Response schema for toggle subscriber video save API.
    """

    is_saved: bool


class MobileWatchProgressRequest(BaseModel):
    """
    Request payload schema for high-frequency watch progress heartbeat API.
    """

    progress_seconds: int = Field(
        ..., ge=0, description="Current playback position in seconds"
    )


class WatchProgressResponse(BaseModel):
    """
    DTO representation for subscriber video watch position and completion percentage.
    """

    last_position_seconds: int = 0
    completion_percentage: float = 0.0


class MobileAdImpressionRequest(BaseModel):
    """
    Request payload for in-stream ad impression telemetry beacon.
    """

    event_type: str = Field(
        default="impression",
        pattern=r"^(impression|midpoint|complete)$",
        description="IMA Ad event milestone: 'impression', 'midpoint', or 'complete'",
    )
    ad_duration_seconds: int = Field(
        default=0,
        ge=0,
        description="Creative duration in seconds",
    )


class CreatorBrandingSummary(BaseModel):
    """
    Creator studio branding summary embedded in shorts feed items.
    """

    name: str
    logo_url: str | None = None


class MobileShortItemResponse(BaseModel):
    """
    Rich vertical video DTO for Mobile Reels / Shorts swipe feed.
    Streams via HLS only. 100% ad-free, no downloads.
    """

    id: int
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    duration: int = 0
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_saved: bool = False
    hls_stream_url: str
    captions: list[MobileVideoCaptionResponse] = Field(default_factory=list)
    creator: CreatorBrandingSummary
    published_at: datetime | None = None
