import logging

from peewee import PeeweeException

from app.config import get_settings
from app.database import db_proxy
from app.models.featured_video import FeaturedVideo
from app.models.video import Video

logger = logging.getLogger(__name__)


class FeaturedVideoRepository:
    """
    Data access layer for Admin Featured Videos curation matching spec doc.
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
            logger.error("Error fetching featured videos for creator %s: %s", creator_id, e)
            return []

    def get_featured_count(self, creator_id: int) -> int:
        """
        Returns total count of featured videos for creator_id.
        """
        try:
            return FeaturedVideo.select().where(FeaturedVideo.creator == creator_id).count()
        except PeeweeException as e:
            logger.error("Error counting featured videos for creator %s: %s", creator_id, e)
            return 0

    def add_featured_videos(
        self, creator_id: int, video_ids: list[int]
    ) -> tuple[int, int]:
        """
        Validates ownership, checks max cap from settings, and appends valid videos at next position sequence.
        Returns (added_count, new_total).
        """
        try:
            with db_proxy.atomic():
                current_count = self.get_featured_count(creator_id)
                max_allowed = get_settings().MAX_FEATURED_VIDEOS_PER_CREATOR

                # 1 Single SQL Subquery: Find valid videos owned by creator that are not already featured
                valid_videos = list(
                    Video.select().where(
                        (Video.id.in_(video_ids))
                        & (Video.user == creator_id)
                        & (~Video.id.in_(
                            FeaturedVideo.select(FeaturedVideo.video).where(
                                FeaturedVideo.creator == creator_id
                            )
                        ))
                    )
                )

                if not valid_videos:
                    return 0, current_count

                if current_count + len(valid_videos) > max_allowed:
                    raise ValueError(
                        f"Cannot exceed maximum of {max_allowed} featured videos. Currently featured: {current_count}."
                    )

                added_count = 0
                for idx, v in enumerate(valid_videos, start=1):
                    FeaturedVideo.create(
                        creator=creator_id,
                        video=v.id,
                        position=current_count + idx,
                    )
                    added_count += 1

                new_total = current_count + added_count
                return added_count, new_total

        except PeeweeException as e:
            logger.error("Error adding featured videos for creator %s: %s", creator_id, e)
            raise

    def reorder_featured_videos(self, creator_id: int, video_ids: list[int]) -> bool:
        """
        Batch updates position sequence for featured videos belonging to creator_id.
        """
        try:
            with db_proxy.atomic():
                for position, v_id in enumerate(video_ids, start=1):
                    FeaturedVideo.update(position=position).where(
                        (FeaturedVideo.creator == creator_id)
                        & (FeaturedVideo.video == v_id)
                    ).execute()
            return True
        except PeeweeException as e:
            logger.error("Error reordering featured videos for creator %s: %s", creator_id, e)
            raise

    def delete_featured_video(self, creator_id: int, video_id: int) -> bool:
        """
        Deletes a video from creator's featured list and compacts remaining positions.
        """
        return self.bulk_delete_featured_videos(creator_id, [video_id]) > 0

    def bulk_delete_featured_videos(self, creator_id: int, video_ids: list[int]) -> int:
        """
        Deletes multiple videos from creator's featured list and compacts remaining positions sequence.
        Returns deleted count.
        """
        try:
            with db_proxy.atomic():
                deleted_count = (
                    FeaturedVideo.delete()
                    .where(
                        (FeaturedVideo.creator == creator_id)
                        & (FeaturedVideo.video.in_(video_ids))
                    )
                    .execute()
                )
                if deleted_count > 0:
                    # Re-compact position sequence
                    remaining = (
                        FeaturedVideo.select()
                        .where(FeaturedVideo.creator == creator_id)
                        .order_by(FeaturedVideo.position.asc())
                    )
                    for pos, fv in enumerate(remaining, start=1):
                        fv.position = pos
                        fv.save()
                return deleted_count
        except PeeweeException as e:
            logger.error("Error bulk deleting featured videos %s for creator %s: %s", video_ids, creator_id, e)
            raise

    def get_available_videos_for_featured(
        self,
        creator_id: int,
        search: str | None = None,
        category: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Retrieves paginated published videos owned by creator that are NOT in featured list.
        Supports sorting by newest, oldest, popular/most_viewed, and most_liked.
        """
        try:
            featured_subquery = FeaturedVideo.select(FeaturedVideo.video).where(
                FeaturedVideo.creator == creator_id
            )

            query = Video.select().where(
                (Video.user == creator_id)
                & (Video.status == "published")
                & (~Video.id.in_(featured_subquery))
            )

            if search:
                query = query.where(Video.title.contains(search))

            if category:
                query = query.where(Video.category == category)

            total = query.count()

            # Dynamic Sort Ordering matching platform standard
            sort_lower = sort.lower().strip() if sort else "newest"
            if sort_lower == "oldest":
                order_expr = [Video.created_at.asc(), Video.id.asc()]
            elif sort_lower == "popular":
                order_expr = [Video.popularity_score.desc(), Video.views.desc(), Video.id.desc()]
            elif sort_lower == "most_viewed":
                order_expr = [Video.views.desc(), Video.created_at.desc(), Video.id.desc()]
            elif sort_lower == "most_liked":
                order_expr = [Video.likes.desc(), Video.views.desc(), Video.id.desc()]
            else:  # newest
                order_expr = [Video.created_at.desc(), Video.id.desc()]

            videos = list(query.order_by(*order_expr).paginate(page, limit))
            return videos, total
        except PeeweeException as e:
            logger.error("Error fetching available videos for featured: %s", e)
            return [], 0
