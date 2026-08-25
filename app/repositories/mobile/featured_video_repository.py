import logging

from peewee import PeeweeException, Value, fn

from app.models.featured_video import FeaturedVideo
from app.models.video import Video, VideoLike, VideoSave

logger = logging.getLogger(__name__)


class MobileFeaturedVideoRepository:
    """
    Data access layer for Mobile Subscribers fetching Home Screen Featured Video Carousel.
    """

    def get_featured_videos(
        self, creator_id: int, subscriber_id: int | None = None
    ) -> list[dict]:
        """
        Retrieves creator featured videos in 1 SINGLE SQL query, enriched with description and subscriber interaction flags.
        """
        try:
            # 1-Query SQL Subquery Expressions for Subscriber Flags
            is_liked_expr = (
                fn.EXISTS(
                    VideoLike.select().where(
                        (VideoLike.video == Video.id)
                        & (VideoLike.subscriber == subscriber_id)
                    )
                )
                if subscriber_id
                else Value(False)
            )

            is_saved_expr = (
                fn.EXISTS(
                    VideoSave.select().where(
                        (VideoSave.video == Video.id)
                        & (VideoSave.subscriber == subscriber_id)
                    )
                )
                if subscriber_id
                else Value(False)
            )

            query = (
                FeaturedVideo.select(
                    FeaturedVideo,
                    Video,
                    is_liked_expr.alias("is_liked"),
                    is_saved_expr.alias("is_saved"),
                )
                .join(Video)
                .where(
                    (FeaturedVideo.creator == creator_id)
                    & (
                        (fn.LOWER(Video.status).in_(["published", "ready"]))
                        | (Video.is_playable == True)
                    )
                )
                .order_by(FeaturedVideo.position.asc(), FeaturedVideo.created_at.asc())
            )

            result = []
            for row in query:
                v = row.video
                result.append(
                    {
                        "id": v.id,
                        "position": row.position,
                        "title": v.title,
                        "description": v.description,
                        "category": v.category,
                        "main_thumbnail_url": v.main_thumbnail_url,
                        "duration": v.duration,
                        "views": v.views or 0,
                        "likes": v.likes or 0,
                        "is_liked": bool(getattr(row, "is_liked", False)),
                        "is_saved": bool(getattr(row, "is_saved", False)),
                        "created_at": v.created_at,
                    }
                )

            return result
        except PeeweeException as e:
            logger.error("Error fetching mobile featured videos for creator %s: %s", creator_id, e)
            return []
