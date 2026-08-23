import logging
from datetime import datetime, timezone

from peewee import PeeweeException, fn

from app.models.video import Video, VideoLike, VideoSave, WatchHistory
from app.utils.formatters import parse_duration_seconds

logger = logging.getLogger(__name__)


class MobileVideoRepository:
    """
    Data access repository for Mobile Subscriber Video catalog & streaming playback.
    Strictly filters videos where status == 'published' AND transcoding_status == 'READY'.
    """

    def list_public_videos(
        self,
        creator_id: int | None = None,
        category: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Retrieves paginated public videos filtered by creator_id, published state, and readiness.
        Supports Option 1 Popularity Score (views + 3*likes) and Option 2 (most_liked).
        """
        try:
            query = Video.select().where(
                (fn.LOWER(Video.status).in_(["published", "ready"]))
                & (Video.is_playable == True)
            )

            if creator_id is not None:
                query = query.where(Video.user == creator_id)

            if category:
                query = query.where(fn.LOWER(Video.category) == category.lower())

            if search:
                query = query.where(
                    (Video.title.contains(search))
                    | (Video.description.contains(search))
                )

            total_count = query.count()

            # Sort ordering algorithms using indexed Video.popularity_score column
            if sort == "popular":
                query = query.order_by(Video.popularity_score.desc(), Video.id.desc())
            elif sort == "most_liked":
                query = (
                    query.select(Video, fn.COUNT(VideoLike.id).alias("likes_cnt"))
                    .join(
                        VideoLike,
                        on=(Video.id == VideoLike.video),
                        join_type="LEFT OUTER",
                    )
                    .group_by(Video.id)
                    .order_by(
                        fn.COUNT(VideoLike.id).desc(),
                        Video.views.desc(),
                        Video.id.desc(),
                    )
                )
            elif sort == "oldest":
                query = query.order_by(Video.published_at.asc(), Video.id.asc())
            else:
                # Default "newest"
                query = query.order_by(Video.published_at.desc(), Video.id.desc())

            videos = list(query.paginate(page, limit))
            return videos, total_count
        except PeeweeException as e:
            logger.error("Error querying public mobile videos: %s", e)
            raise

    def list_subscriber_liked_videos(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Retrieves paginated published & ready videos liked by a specific subscriber ("My Liked Videos").
        Optionally filters by creator_id for tenant isolation.
        """
        try:
            query = (
                Video.select()
                .join(VideoLike, on=(Video.id == VideoLike.video))
                .where(
                    (VideoLike.subscriber == subscriber_id)
                    & (fn.LOWER(Video.status).in_(["published", "ready"]))
                    & (Video.is_playable == True)
                )
            )

            if creator_id is not None:
                query = query.where(Video.user == creator_id)

            query = query.order_by(VideoLike.created_at.desc())

            total_count = query.count()
            videos = list(query.paginate(page, limit))
            return videos, total_count
        except PeeweeException as e:
            logger.error(
                "Error querying subscriber liked videos for subscriber %s: %s",
                subscriber_id,
                e,
            )
            raise

    def get_public_video_by_id(
        self, video_id: int, creator_id: int | None = None
    ) -> Video | None:
        """
        Fetches a single published & ready video by primary key ID, optionally filtered by creator_id for tenant isolation.
        """
        try:
            query = Video.select().where(
                (Video.id == video_id)
                & (fn.LOWER(Video.status).in_(["published", "ready"]))
                & (Video.is_playable == True)
            )

            if creator_id is not None:
                query = query.where(Video.user == creator_id)

            return query.first()
        except PeeweeException as e:
            logger.error("Error fetching public video %s: %s", video_id, e)
            raise

    def increment_view_count(
        self, video_id: int, creator_id: int | None = None
    ) -> int | None:
        """
        Atomically increments views for a published video and updates its stored popularity_score.
        """
        video = self.get_public_video_by_id(video_id, creator_id=creator_id)
        if not video:
            return None

        video.views = (video.views or 0) + 1
        likes_count = self.get_video_likes_count(video_id)
        video.popularity_score = video.views + (3 * likes_count)
        video.save()
        return video.views

    def get_video_likes_count(self, video_id: int) -> int:
        """
        Returns total likes count for a video asset.
        """
        return VideoLike.select().where(VideoLike.video == video_id).count()

    def is_video_liked_by_subscriber(self, video_id: int, subscriber_id: int) -> bool:
        """
        Checks if a specific subscriber has liked a video asset.
        """
        return (
            VideoLike.select()
            .where(
                (VideoLike.video == video_id) & (VideoLike.subscriber == subscriber_id)
            )
            .exists()
        )

    def toggle_video_like(
        self, video_id: int, subscriber_id: int, creator_id: int | None = None
    ) -> tuple[bool, int] | None:
        """
        Toggles subscriber like state for a video asset in DB and updates its stored popularity_score.
        Returns (is_liked: bool, total_likes_count: int) or None if video not found.
        """
        try:
            video = self.get_public_video_by_id(video_id, creator_id=creator_id)
            if not video:
                return None

            existing_like = VideoLike.get_or_none(
                (VideoLike.video == video_id) & (VideoLike.subscriber == subscriber_id)
            )

            if existing_like:
                existing_like.delete_instance()
                is_liked = False
            else:
                VideoLike.create(video=video_id, subscriber=subscriber_id)
                is_liked = True

            total_likes = self.get_video_likes_count(video_id)
            video.popularity_score = (video.views or 0) + (3 * total_likes)
            video.save()

            return is_liked, total_likes
        except PeeweeException as e:
            logger.error(
                f"Error toggling video like for video {video_id}, subscriber {subscriber_id}: {e!s}"
            )
            raise

    def is_video_saved_by_subscriber(self, video_id: int, subscriber_id: int) -> bool:
        """
        Checks if a specific subscriber has saved/bookmarked a video asset.
        """
        return (
            VideoSave.select()
            .where(
                (VideoSave.video == video_id) & (VideoSave.subscriber == subscriber_id)
            )
            .exists()
        )

    def toggle_video_save(
        self, video_id: int, subscriber_id: int, creator_id: int | None = None
    ) -> bool | None:
        """
        Toggles subscriber save/bookmark state for a video asset in DB.
        Returns is_saved: bool or None if video not found.
        """
        try:
            video = self.get_public_video_by_id(video_id, creator_id=creator_id)
            if not video:
                return None

            existing_save = VideoSave.get_or_none(
                (VideoSave.video == video_id) & (VideoSave.subscriber == subscriber_id)
            )

            if existing_save:
                existing_save.delete_instance()
                return False
            else:
                VideoSave.create(video=video_id, subscriber=subscriber_id)
                return True
        except PeeweeException as e:
            logger.error(
                f"Error toggling video save for video {video_id}, subscriber {subscriber_id}: {e!s}"
            )
            raise

    def list_subscriber_saved_videos(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Retrieves paginated published & ready videos saved by a specific subscriber ("My Watchlist").
        Optionally filters by creator_id for tenant isolation.
        """
        try:
            query = (
                Video.select()
                .join(VideoSave, on=(Video.id == VideoSave.video))
                .where(
                    (VideoSave.subscriber == subscriber_id)
                    & (fn.LOWER(Video.status).in_(["published", "ready"]))
                    & (Video.is_playable == True)
                )
            )

            if creator_id is not None:
                query = query.where(Video.user == creator_id)

            query = query.order_by(VideoSave.created_at.desc())

            total_count = query.count()
            videos = list(query.paginate(page, limit))
            return videos, total_count
        except PeeweeException as e:
            logger.error(
                f"Error querying subscriber saved videos for subscriber {subscriber_id}: {e!s}"
            )
            raise

    def update_watch_progress(
        self,
        video_id: int,
        subscriber_id: int,
        progress_seconds: int,
        creator_id: int | None = None,
    ) -> bool:
        """
        Validates video exists and belongs to creator_id, calculates duration/completion percentage,
        and atomically upserts watch progress in WatchHistory.
        Returns False if video is not found or unauthorized.
        """
        try:
            video = self.get_public_video_by_id(video_id, creator_id=creator_id)
            if not video:
                return False

            duration_seconds = parse_duration_seconds(video.duration)
            now = datetime.now(timezone.utc)
            completed = False
            if duration_seconds > 0:
                progress_pct = (progress_seconds / float(duration_seconds)) * 100.0
                if progress_pct >= 95.0:
                    completed = True

            history_record = WatchHistory.get_or_none(
                (WatchHistory.video == video_id)
                & (WatchHistory.subscriber == subscriber_id)
            )

            if history_record:
                history_record.last_position_seconds = progress_seconds
                history_record.completed = completed
                history_record.last_watched_at = now
                history_record.save()
            else:
                WatchHistory.create(
                    video=video_id,
                    subscriber=subscriber_id,
                    last_position_seconds=progress_seconds,
                    completed=completed,
                    last_watched_at=now,
                )

            return True
        except PeeweeException as e:
            logger.error(
                f"Error updating watch progress for video {video_id}, subscriber {subscriber_id}: {e!s}"
            )
            raise

    def get_subscriber_video_watch_progress(
        self, video_id: int, subscriber_id: int
    ) -> tuple[int, float]:
        """
        Retrieves watch progress tuple (last_position_seconds, progress_percentage) for a subscriber.
        """
        history_record = (
            WatchHistory.select(WatchHistory, Video)
            .join(Video)
            .where(
                (WatchHistory.video == video_id)
                & (WatchHistory.subscriber == subscriber_id)
            )
            .first()
        )
        if not history_record:
            return 0, 0.0

        return self._calc_progress_tuple(history_record)

    def _calc_progress_tuple(self, wh: WatchHistory) -> tuple[int, float]:
        """
        Helper extracting last position seconds and progress percentage for a watch history record.
        """
        pos = wh.last_position_seconds or 0
        dur = parse_duration_seconds(wh.video.duration)
        pct = round(min(100.0, (pos / float(dur)) * 100.0), 1) if dur > 0 else 0.0
        return pos, pct

    def get_subscriber_watch_progress_map(
        self, subscriber_id: int, video_ids: list[int]
    ) -> dict[int, tuple[int, float]]:
        """
        Fetches watch progress (last_position_seconds, progress_percentage) map for subscriber videos.
        """
        if not video_ids:
            return {}
        records = (
            WatchHistory.select(WatchHistory, Video)
            .join(Video)
            .where(
                (WatchHistory.subscriber == subscriber_id)
                & (WatchHistory.video.in_(video_ids))
            )
        )
        return {r.video_id: self._calc_progress_tuple(r) for r in records}

    def list_continue_watching_videos(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[tuple[Video, int, float]], int]:
        """
        Retrieves paginated unfinished videos for subscriber 'Continue Watching' carousel.
        Optionally filters by creator_id for tenant isolation.
        """
        try:
            query = (
                WatchHistory.select(WatchHistory, Video)
                .join(Video)
                .where(
                    (WatchHistory.subscriber == subscriber_id)
                    & (WatchHistory.completed == False)
                    & (WatchHistory.last_position_seconds >= 10)
                    & (fn.LOWER(Video.status).in_(["published", "ready"]))
                    & (Video.is_playable == True)
                )
            )

            if creator_id is not None:
                query = query.where(Video.user == creator_id)

            query = query.order_by(WatchHistory.last_watched_at.desc())

            total_count = query.count()
            records = list(query.paginate(page, limit))
            items = [(wh.video, *self._calc_progress_tuple(wh)) for wh in records]
            return items, total_count
        except PeeweeException as e:
            logger.error(
                f"Error querying continue watching for subscriber {subscriber_id}: {e!s}"
            )
            raise

    def list_watch_history(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[tuple[Video, int, float]], int]:
        """
        Retrieves paginated watch history for subscriber.
        Optionally filters by creator_id for tenant isolation.
        """
        try:
            query = (
                WatchHistory.select(WatchHistory, Video)
                .join(Video)
                .where(
                    (WatchHistory.subscriber == subscriber_id)
                    & (fn.LOWER(Video.status).in_(["published", "ready"]))
                    & (Video.is_playable == True)
                )
            )

            if creator_id is not None:
                query = query.where(Video.user == creator_id)

            query = query.order_by(WatchHistory.last_watched_at.desc())

            total_count = query.count()
            records = list(query.paginate(page, limit))
            items = [(wh.video, *self._calc_progress_tuple(wh)) for wh in records]
            return items, total_count
        except PeeweeException as e:
            logger.error(
                f"Error querying watch history for subscriber {subscriber_id}: {e!s}"
            )
            raise

    def clear_watch_history(
        self, subscriber_id: int, creator_id: int | None = None
    ):
        """
        Deletes all watch history records for a subscriber, scoped by creator_id tenant context.
        """
        try:
            query = WatchHistory.delete().where(
                WatchHistory.subscriber == subscriber_id
            )
            if creator_id is not None:
                creator_videos = Video.select(Video.id).where(
                    Video.user == creator_id
                )
                query = query.where(WatchHistory.video.in_(creator_videos))
            query.execute()
        except PeeweeException as e:
            logger.error(
                f"Error clearing watch history for subscriber {subscriber_id}: {e!s}"
            )
            raise

    def remove_video_from_watch_history(
        self, video_id: int, subscriber_id: int, creator_id: int | None = None
    ) -> bool:
        """
        Deletes a single video watch history record for a subscriber.
        Returns False if video not found or unauthorized.
        """
        try:
            video = self.get_public_video_by_id(video_id, creator_id=creator_id)
            if not video:
                return False

            deleted_count = (
                WatchHistory.delete()
                .where(
                    (WatchHistory.video == video_id)
                    & (WatchHistory.subscriber == subscriber_id)
                )
                .execute()
            )
            return True
        except PeeweeException as e:
            logger.error(
                f"Error removing video {video_id} from watch history for subscriber {subscriber_id}: {e!s}"
            )
            raise
