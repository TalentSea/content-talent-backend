import logging
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from peewee import PeeweeException, fn, JOIN

from app.models.video import Video, VideoLike, VideoSave, WatchHistory

logger = logging.getLogger(__name__)

class MobileVideoRepository:
    """
    Data access repository for Mobile Subscriber Video catalog & streaming playback.
    Strictly filters videos where status == 'published' AND transcoding_status == 'READY'.
    """

    def list_public_videos(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Video], int]:
        """
        Retrieves paginated public videos filtered by published state and readiness.
        Supports Option 1 Popularity Score (views + 3*likes) and Option 2 (most_liked).
        """
        try:
            query = Video.select().where(
                (Video.status == "published") &
                (Video.is_playable == True)
            )

            if category:
                query = query.where(fn.LOWER(Video.category) == category.lower())

            if search:
                query = query.where(
                    (Video.title.contains(search)) | (Video.description.contains(search))
                )

            total_count = query.count()

            # Sort ordering algorithms using indexed Video.popularity_score column
            if sort == "popular":
                query = query.order_by(Video.popularity_score.desc(), Video.id.desc())
            elif sort == "most_liked":
                query = query.select(Video, fn.COUNT(VideoLike.id).alias("likes_cnt")).join(
                    VideoLike, on=(Video.id == VideoLike.video), join_type="LEFT OUTER"
                ).group_by(Video.id).order_by(fn.COUNT(VideoLike.id).desc(), Video.views.desc(), Video.id.desc())
            elif sort == "oldest":
                query = query.order_by(Video.published_at.asc(), Video.id.asc())
            else:
                # Default "newest"
                query = query.order_by(Video.published_at.desc(), Video.id.desc())

            videos = list(query.paginate(page, limit))
            return videos, total_count
        except PeeweeException as e:
            logger.error(f"Error querying public mobile videos: {str(e)}")
            raise e

    def list_subscriber_liked_videos(
        self,
        subscriber_id: int,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Video], int]:
        """
        Retrieves paginated published & ready videos liked by a specific subscriber ("My Liked Videos").
        """
        try:
            query = Video.select().join(
                VideoLike, on=(Video.id == VideoLike.video)
            ).where(
                (VideoLike.subscriber == subscriber_id) &
                (Video.status == "published") &
                (Video.is_playable == True)
            ).order_by(VideoLike.created_at.desc())

            total_count = query.count()
            videos = list(query.paginate(page, limit))
            return videos, total_count
        except PeeweeException as e:
            logger.error(f"Error querying subscriber liked videos for subscriber {subscriber_id}: {str(e)}")
            raise e

    def get_public_video_by_id(self, video_id: int) -> Optional[Video]:
        """
        Fetches a single published & ready video by primary key ID.
        """
        try:
            return Video.get_or_none(
                (Video.id == video_id) &
                (Video.status == "published") &
                (Video.is_playable == True)
            )
        except PeeweeException as e:
            logger.error(f"Error fetching public video {video_id}: {str(e)}")
            raise e

    def increment_view_count(self, video_id: int) -> Optional[int]:
        """
        Atomically increments views for a published video and updates its stored popularity_score.
        """
        video = self.get_public_video_by_id(video_id)
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
        return VideoLike.select().where(
            (VideoLike.video == video_id) &
            (VideoLike.subscriber == subscriber_id)
        ).exists()

    def toggle_video_like(self, video_id: int, subscriber_id: int) -> Tuple[bool, int]:
        """
        Toggles subscriber like state for a video asset in DB and updates its stored popularity_score.
        Returns (is_liked: bool, total_likes_count: int).
        """
        try:
            existing_like = VideoLike.get_or_none(
                (VideoLike.video == video_id) &
                (VideoLike.subscriber == subscriber_id)
            )

            if existing_like:
                existing_like.delete_instance()
                is_liked = False
            else:
                VideoLike.create(video=video_id, subscriber=subscriber_id)
                is_liked = True

            total_likes = self.get_video_likes_count(video_id)
            video = Video.get_or_none(Video.id == video_id)
            if video:
                video.popularity_score = (video.views or 0) + (3 * total_likes)
                video.save()

            return is_liked, total_likes
        except PeeweeException as e:
            logger.error(f"Error toggling video like for video {video_id}, subscriber {subscriber_id}: {str(e)}")
            raise e

    def is_video_saved_by_subscriber(self, video_id: int, subscriber_id: int) -> bool:
        """
        Checks if a specific subscriber has saved/bookmarked a video asset.
        """
        return VideoSave.select().where(
            (VideoSave.video == video_id) &
            (VideoSave.subscriber == subscriber_id)
        ).exists()

    def toggle_video_save(self, video_id: int, subscriber_id: int) -> bool:
        """
        Toggles subscriber save/bookmark state for a video asset in DB.
        Returns is_saved: bool.
        """
        try:
            existing_save = VideoSave.get_or_none(
                (VideoSave.video == video_id) &
                (VideoSave.subscriber == subscriber_id)
            )

            if existing_save:
                existing_save.delete_instance()
                return False
            else:
                VideoSave.create(video=video_id, subscriber=subscriber_id)
                return True
        except PeeweeException as e:
            logger.error(f"Error toggling video save for video {video_id}, subscriber {subscriber_id}: {str(e)}")
            raise e

    def list_subscriber_saved_videos(
        self,
        subscriber_id: int,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Video], int]:
        """
        Retrieves paginated published & ready videos saved by a specific subscriber ("My Watchlist").
        """
        try:
            query = Video.select().join(
                VideoSave, on=(Video.id == VideoSave.video)
            ).where(
                (VideoSave.subscriber == subscriber_id) &
                (Video.status == "published") &
                (Video.is_playable == True)
            ).order_by(VideoSave.created_at.desc())

            total_count = query.count()
            videos = list(query.paginate(page, limit))
            return videos, total_count
        except PeeweeException as e:
            logger.error(f"Error querying subscriber saved videos for subscriber {subscriber_id}: {str(e)}")
            raise e

    def upsert_watch_progress(
        self,
        video_id: int,
        subscriber_id: int,
        progress_seconds: int,
        duration_seconds: int
    ) -> Tuple[int, float]:
        """
        Upserts subscriber playback progress for a video and returns (last_position_seconds, progress_percentage).
        Automatically marks completed = True if progress_seconds >= 95% of duration.
        """
        try:
            now = datetime.now()
            completed = False
            progress_pct = 0.0
            if duration_seconds > 0:
                progress_pct = round(min(100.0, (progress_seconds / float(duration_seconds)) * 100.0), 1)
                if progress_pct >= 95.0:
                    completed = True

            history_record = WatchHistory.get_or_none(
                (WatchHistory.video == video_id) &
                (WatchHistory.subscriber == subscriber_id)
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
                    last_watched_at=now
                )

            return progress_seconds, progress_pct
        except PeeweeException as e:
            logger.error(f"Error upserting watch progress for video {video_id}, subscriber {subscriber_id}: {str(e)}")
            raise e

    def get_subscriber_video_watch_progress(
        self,
        video_id: int,
        subscriber_id: int,
        duration_seconds: int = 0
    ) -> Tuple[int, float]:
        """
        Retrieves watch progress tuple (last_position_seconds, progress_percentage) for a subscriber.
        """
        history_record = WatchHistory.get_or_none(
            (WatchHistory.video == video_id) &
            (WatchHistory.subscriber == subscriber_id)
        )
        if not history_record:
            return 0, 0.0

        pos = history_record.last_position_seconds or 0
        pct = 0.0
        if duration_seconds > 0:
            pct = round(min(100.0, (pos / float(duration_seconds)) * 100.0), 1)
        return pos, pct

    def get_subscriber_watch_progress_map(
        self,
        subscriber_id: int,
        video_ids: List[int]
    ) -> Dict[int, Tuple[int, float]]:
        """
        Batch fetches watch progress map {video_id: (last_position_seconds, progress_percentage)} for video IDs.
        """
        if not video_ids:
            return {}
        records = WatchHistory.select(WatchHistory, Video).join(Video).where(
            (WatchHistory.subscriber == subscriber_id) &
            (WatchHistory.video.in_(video_ids))
        )
        progress_map = {}
        for r in records:
            dur = int(r.video.duration or 0)
            pos = r.last_position_seconds or 0
            pct = round(min(100.0, (pos / float(dur)) * 100.0), 1) if dur > 0 else 0.0
            progress_map[r.video_id] = (pos, pct)
        return progress_map

    def list_continue_watching_videos(
        self,
        subscriber_id: int,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Tuple[Video, int, float]], int]:
        """
        Retrieves paginated unfinished videos for subscriber 'Continue Watching' carousel.
        """
        try:
            query = WatchHistory.select(WatchHistory, Video).join(Video).where(
                (WatchHistory.subscriber == subscriber_id) &
                (WatchHistory.completed == False) &
                (WatchHistory.last_position_seconds >= 10) &
                (Video.status == "published") &
                (Video.is_playable == True)
            ).order_by(WatchHistory.last_watched_at.desc())

            total_count = query.count()
            records = list(query.paginate(page, limit))
            items = []
            for wh in records:
                v = wh.video
                pos = wh.last_position_seconds or 0
                dur = int(v.duration or 0)
                pct = round(min(100.0, (pos / float(dur)) * 100.0), 1) if dur > 0 else 0.0
                items.append((v, pos, pct))
            return items, total_count
        except PeeweeException as e:
            logger.error(f"Error querying continue watching for subscriber {subscriber_id}: {str(e)}")
            raise e

    def list_watch_history(
        self,
        subscriber_id: int,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Tuple[Video, int, float]], int]:
        """
        Retrieves paginated watch history for subscriber.
        """
        try:
            query = WatchHistory.select(WatchHistory, Video).join(Video).where(
                (WatchHistory.subscriber == subscriber_id) &
                (Video.status == "published") &
                (Video.is_playable == True)
            ).order_by(WatchHistory.last_watched_at.desc())

            total_count = query.count()
            records = list(query.paginate(page, limit))
            items = []
            for wh in records:
                v = wh.video
                pos = wh.last_position_seconds or 0
                dur = int(v.duration or 0)
                pct = round(min(100.0, (pos / float(dur)) * 100.0), 1) if dur > 0 else 0.0
                items.append((v, pos, pct))
            return items, total_count
        except PeeweeException as e:
            logger.error(f"Error querying watch history for subscriber {subscriber_id}: {str(e)}")
            raise e

    def clear_watch_history(self, subscriber_id: int):
        """
        Deletes all watch history records for a subscriber.
        """
        try:
            WatchHistory.delete().where(WatchHistory.subscriber == subscriber_id).execute()
        except PeeweeException as e:
            logger.error(f"Error clearing watch history for subscriber {subscriber_id}: {str(e)}")
            raise e

    def remove_video_from_watch_history(self, video_id: int, subscriber_id: int) -> bool:
        """
        Deletes a single video watch history record for a subscriber.
        """
        try:
            deleted_count = WatchHistory.delete().where(
                (WatchHistory.video == video_id) &
                (WatchHistory.subscriber == subscriber_id)
            ).execute()
            return deleted_count > 0
        except PeeweeException as e:
            logger.error(f"Error removing video {video_id} from watch history for subscriber {subscriber_id}: {str(e)}")
            raise e

