from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ThumbnailSlotInput(BaseModel):
    slot: int = Field(..., description="0: Main Cover, 1: Alt 1, 2: Alt 2")
    filename: str

class VideoInitiateRequest(BaseModel):
    """Request payload for initiating a video upload."""
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    thumbnails: Optional[List[ThumbnailSlotInput]] = []

class VideoInitiateResponse(BaseModel):
    """Response payload returned after video upload initiation."""
    id: int
    bunny_video_id: str
    bunny_library_id: str
    status: str
    signature: str
    expiration_time: int
    main_thumbnail_url: Optional[str] = None
    alt_thumbnail_urls: List[str] = []

class VideoResponse(BaseModel):
    """Canonical DTO for returning video asset details."""
    id: int
    bunny_video_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    status: str
    encode_progress: int
    is_playable: bool
    playback_url: Optional[str] = None
    main_thumbnail_url: Optional[str] = None
    alt_thumbnail_urls: List[str] = []
    created_at: Optional[datetime] = None

class VideoUpdateRequest(BaseModel):
    """Request payload for updating video textual metadata."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class ThumbnailUploadUrlRequest(BaseModel):
    """Request payload for requesting a presigned thumbnail upload URL."""
    slot: int = Field(..., description="0: Main Cover, 1: Alt 1, 2: Alt 2")
    filename: str

class ThumbnailUploadUrlResponse(BaseModel):
    """Response payload containing presigned thumbnail upload URL."""
    slot: int
    thumbnail_url: str
    image_upload_url: str

class SelectMainThumbnailRequest(BaseModel):
    """Request payload for selecting a new main cover thumbnail."""
    selected_main_thumbnail: str

class DeleteThumbnailRequest(BaseModel):
    """Request payload for deleting an alternative backup thumbnail."""
    thumbnail_url: str

class BunnyWebhookPayload(BaseModel):
    """Payload envelope sent by Bunny Stream webhook events."""
    VideoLibraryId: int
    VideoGuid: str
    Status: int
