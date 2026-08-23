from datetime import datetime

from pydantic import BaseModel, Field


class FeaturedVideoAddRequest(BaseModel):
    """
    Request payload to add video(s) to creator's featured list.
    """

    video_ids: list[int] = Field(
        ..., min_items=1, description="List of video IDs to add to featured list"
    )


class FeaturedVideoReorderRequest(BaseModel):
    """
    Request payload to reorder positions of featured videos.
    """

    video_ids: list[int] = Field(
        ..., min_items=1, description="List of video IDs in new position sequence"
    )


class FeaturedVideoBulkDeleteRequest(BaseModel):
    """
    Request payload to bulk delete video(s) from featured list.
    """

    video_ids: list[int] = Field(
        ..., min_items=1, description="List of video IDs to remove from featured list"
    )


class FeaturedVideoItemResponse(BaseModel):
    """
    DTO representing a video currently in the creator's featured carousel list.
    """

    id: int
    video_id: int
    position: int
    title: str
    category: str | None = None
    main_thumbnail_url: str | None = None
    duration: str | None = None
    views: int = 0
    likes: int = 0
    status: str
    created_at: datetime | None = None


class FeaturedVideoAddResponse(BaseModel):
    """
    Response returned after adding videos to featured list.
    """

    status: str = "success"
    added_count: int
    total_featured: int


class FeaturedAvailableVideoResponse(BaseModel):
    """
    DTO for available published videos picker endpoint.
    """

    id: int
    title: str
    category: str | None = None
    duration: str | None = None
    main_thumbnail_url: str | None = None
    views: int = 0
    likes: int = 0
    created_at: datetime | None = None
