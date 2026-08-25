from datetime import datetime

from pydantic import BaseModel


class FeaturedVideoSyncRequest(BaseModel):
    """
    Request payload for synchronizing the active featured videos list matching spec doc API 3.2.
    Passing an ordered array of video_ids replaces the creator's featured list in exact sequence.
    """

    video_ids: list[int]


class FeaturedVideoItemResponse(BaseModel):
    """
    Response DTO representing a single featured video item matching spec doc API 3.1 & 3.2.
    """

    id: int
    video_id: int
    position: int
    title: str
    description: str | None = None
    category: str | None = None
    main_thumbnail_url: str | None = None
    duration: str | None = None
    views: int = 0
    likes: int = 0
    status: str
    created_at: datetime | None = None


class FeaturedVideoSyncResponse(BaseModel):
    """
    Response envelope returned after synchronizing featured videos matching spec doc API 3.2.
    """

    status: str = "success"
    total_featured: int
    items: list[FeaturedVideoItemResponse]


class FeaturedAvailableVideoResponse(BaseModel):
    """
    Response DTO representing an unattached video in the available picker modal matching spec doc API 3.3.
    """

    id: int
    title: str
    category: str | None = None
    duration: str | None = None
    main_thumbnail_url: str | None = None
    views: int = 0
    likes: int = 0
    created_at: datetime | None = None
