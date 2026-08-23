import logging

from app.repositories.mobile_featured_video_repository import (
    MobileFeaturedVideoRepository,
)
from app.schemas.mobile_featured_video_schemas import MobileFeaturedVideoResponse

logger = logging.getLogger(__name__)


class MobileFeaturedVideoService:
    """
    Business logic layer for Mobile Subscribers fetching Home Screen Featured Video Carousel.
    """

    def __init__(self, repo: MobileFeaturedVideoRepository | None = None) -> None:
        self.repo = repo or MobileFeaturedVideoRepository()

    def get_featured_videos(
        self, creator_id: int, subscriber_id: int | None = None
    ) -> list[MobileFeaturedVideoResponse]:
        """
        Retrieves creator featured videos for mobile home screen carousel matching spec doc.
        """
        items = self.repo.get_featured_videos(
            creator_id=creator_id, subscriber_id=subscriber_id
        )
        return [MobileFeaturedVideoResponse(**item) for item in items]
