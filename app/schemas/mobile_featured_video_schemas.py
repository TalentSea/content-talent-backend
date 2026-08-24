from datetime import datetime

from pydantic import BaseModel


class MobileFeaturedVideoResponse(BaseModel):
    """
    Response DTO representing a featured video item on the mobile home screen carousel,
    enriched with description and subscriber personal interaction flags (is_liked, is_saved).
    """

    id: int
    position: int
    title: str
    description: str | None = None
    category: str | None = None
    main_thumbnail_url: str | None = None
    duration: str | None = None
    views: int = 0
    likes: int = 0
    is_liked: bool = False
    is_saved: bool = False
    created_at: datetime | None = None
