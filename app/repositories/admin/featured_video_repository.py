import logging

from peewee import PeeweeException, fn

from app.config import get_settings
from app.database import db_proxy
from app.models.featured_video import FeaturedVideo
from app.models.video import Video

logger = logging.getLogger(__name__)


class FeaturedVideoRepository:
    """
    Data access layer for Admin Featured Videos curation matching 3-API State Sync design.
    """

    def get_featured_videos(self, creator_id: int) -> list[tuple[FeaturedVideo, Video]]:
        """
        Retrieves all featured video rows for creator_id joined with Video, ordered by position asc.
        """
        try:
            query = (
                FeaturedVideo.select(FeaturedVideo, Video)
                .join(Video)
                .where(FeaturedVideo.creator == creator_id)
                .order_by(FeaturedVideo.position.asc(), FeaturedVideo.created_at.asc())
            )
            return list(query)
        except PeeweeException as e:
            logger.error(
                "Error fetching featured videos for creator %s: %s", creator_id, e
            )
            return []

    def get_featured_count(self, creator_id: int) -> int:
        """
        Returns total count of featured videos for creator_id.
        """
        try:
            return (
                FeaturedVideo.select()
                .where(FeaturedVideo.creator == creator_id)
                .count()
            )
        except PeeweeException as e:
            logger.error(
                "Error counting featured videos for creator %s: %s", creator_id, e
            )
            return 0

    def sync_featured_videos(
        self, creator_id: int, video_ids: list[int]
    ) -> list[tuple[FeaturedVideo, Video]]:
        """
        Full State Sync: Replaces all active featured videos for creator_id with new payload in 1 atomic transaction.
        Validates ownership, enforces max cap from settings, and bulk inserts new rows.
        """
        try:
            max_allowed = get_settings().MAX_FEATURED_VIDEOS_PER_CREATOR
            unique_ids = []
            for vid in video_ids:
                if vid not in unique_ids:
                    unique_ids.append(vid)
            unique_ids = unique_ids[:max_allowed]

            with db_proxy.atomic():
                # 1. Fetch valid videos owned by creator
                if unique_ids:
                    valid_videos_dict = {
                        v.id: v
                        for v in Video.select().where(
                            (Video.user == creator_id)
                            & (Video.id.in_(unique_ids))
                            & (
                                (fn.LOWER(Video.status).in_(["published", "ready"]))
                                | (Video.is_playable == True)
                            )
                        )
                    }
                    ordered_videos = [
                        valid_videos_dict[vid]
                        for vid in unique_ids
                        if vid in valid_videos_dict
                    ]
                else:
                    ordered_videos = []

                # 2. Clear existing featured records for this creator
                FeaturedVideo.delete().where(
                    FeaturedVideo.creator == creator_id
                ).execute()

                # 3. Bulk insert new rows in 1 single atomic SQL statement
                if ordered_videos:
                    rows_to_insert = [
                        {
                            "creator": creator_id,
                            "video": v.id,
                            "position": idx,
                        }
                        for idx, v in enumerate(ordered_videos, start=1)
                    ]
                    FeaturedVideo.insert_many(rows_to_insert).execute()

            return self.get_featured_videos(creator_id)
        except PeeweeException as e:
            logger.error(
                "Error synchronizing featured videos for creator %s: %s", creator_id, e
            )
            return []

    def get_available_videos_for_featured(
        self,
        creator_id: int,
        search: str | None = None,
        category: str | None = None,
        sort: str | None = "popular",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Executes query returning paginated, filtered, and sorted list of creator videos NOT currently featured.
        """
        try:
            featured_subquery = FeaturedVideo.select(FeaturedVideo.video_id).where(
                FeaturedVideo.creator_id == creator_id
            )
            query = Video.select().where(
                (Video.user == creator_id)
                & (
                    (fn.LOWER(Video.status).in_(["published", "ready"]))
                    | (Video.is_playable == True)
                )
                & (Video.id.not_in(featured_subquery))
            )

            if search:
                query = query.where(Video.title.contains(search))

            if category:
                query = query.where(fn.LOWER(Video.category) == category.lower())

            if sort == "most_viewed":
                query = query.order_by(Video.views.desc(), Video.created_at.desc())
            elif sort == "oldest":
                query = query.order_by(Video.created_at.asc())
            elif sort == "newest":
                query = query.order_by(Video.created_at.desc())
            else:  # default "popular" using B-Tree indexed popularity_score (views + 3*likes)
                query = query.order_by(
                    Video.popularity_score.desc(), Video.created_at.desc()
                )

            total = query.count()
            videos = list(query.paginate(page, limit))
            return videos, total
        except PeeweeException as e:
            logger.error(
                "Error fetching available videos for creator %s: %s", creator_id, e
            )
            return [], 0
