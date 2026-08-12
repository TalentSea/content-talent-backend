from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class MobileVideoListItemResponse(BaseModel):
    """
    Lightweight DTO for mobile video catalog feed & search results.
    """
    id: int
    title: str
    thumbnail_url: Optional[str] = None
    duration: int = 0
    views_count: int = 0
    category: Optional[str] = None
    last_position_seconds: Optional[int] = None
    progress_percentage: Optional[float] = None
    published_at: Optional[datetime] = None

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
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    duration: int = 0
    views_count: int = 0
    likes_count: int = 0
    is_liked: bool = False
    is_saved: bool = False
    last_position_seconds: int = 0
    progress_percentage: float = 0.0
    thumbnail_url: Optional[str] = None
    hls_stream_url: Optional[str] = None
    download_urls: List[MobileVideoDownloadUrlResponse] = Field(default_factory=list)
    captions: List[MobileVideoCaptionResponse] = Field(default_factory=list)
    published_at: Optional[datetime] = None

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
    progress_seconds: int = Field(..., ge=0, description="Current playback position in seconds")

class WatchProgressResponse(BaseModel):
    """
    DTO representation for subscriber video watch position and completion percentage.
    """
    last_position_seconds: int = 0
    completion_percentage: float = 0.0



