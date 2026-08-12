import logging
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from peewee import PeeweeException, fn

from app.models.playlist import Playlist, PlaylistVideo
from app.models.video import Video, VideoLike, VideoSave, WatchHistory

logger = logging.getLogger(__name__)

class MobilePlaylistRepository:
    """
    Data access repository for Mobile Subscriber Playlist Feed & Video Streaming.
    Filters playlists and attached videos to published, ready content.
    """

    def list_public_playlists(
        self,
        search: Optional[str] = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Tuple[Playlist, int]], int]:
        """
        Retrieves paginated public creator playlists with batched count of published & ready videos.
        """
        try:
            query = Playlist.select()

            if search:
                query = query.where(Playlist.name.contains(search))

            if sort == "oldest":
                query = query.order_by(Playlist.created_at.asc())
            elif sort == "title":
                query = query.order_by(Playlist.name.asc())
            else:
                query = query.order_by(Playlist.created_at.desc())

            total = query.count()
            playlists = list(query.paginate(page, limit))
            if not playlists:
                return [], total

            # Batch count only published & ready videos for each playlist
            pl_ids = [p.id for p in playlists]
            counts_query = (
                PlaylistVideo.select(PlaylistVideo.playlist, fn.COUNT(PlaylistVideo.video).alias("v_count"))
                .join(Video, on=(PlaylistVideo.video == Video.id))
                .where(
                    (PlaylistVideo.playlist.in_(pl_ids)) &
                    (Video.status == "published") &
                    (Video.is_playable == True)
                )
                .group_by(PlaylistVideo.playlist)
            )
            counts_map = {row.playlist_id: row.v_count for row in counts_query}

            results = [(p, counts_map.get(p.id, 0)) for p in playlists]
            return results, total
        except PeeweeException as e:
            logger.error(f"Error querying mobile public playlists: {str(e)}")
            raise e

    def get_public_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        """
        Fetches a single playlist by primary key ID.
        """
        try:
            return Playlist.get_or_none(Playlist.id == playlist_id)
        except PeeweeException as e:
            logger.error(f"Error fetching mobile playlist {playlist_id}: {str(e)}")
            raise e

    def get_playlist_videos_with_subscriber_overlay(
        self,
        playlist: Playlist,
        subscriber_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        Retrieves paginated published & ready videos for a playlist with order and subscriber engagement overlay.
        """
        try:
            query = (
                Video.select(Video, PlaylistVideo.order)
                .join(PlaylistVideo, on=(Video.id == PlaylistVideo.video))
                .where(
                    (PlaylistVideo.playlist == playlist) &
                    (Video.status == "published") &
                    (Video.is_playable == True)
                )
                .order_by(PlaylistVideo.order.asc())
            )

            total = query.count()
            paginated_videos = list(query.paginate(page, limit))
            if not paginated_videos:
                return [], total

            video_ids = [v.id for v in paginated_videos]

            # Batch subscriber engagement overlay
            liked_set = set()
            saved_set = set()
            watch_map = {}

            if subscriber_id:
                liked_query = VideoLike.select(VideoLike.video).where(
                    (VideoLike.subscriber == subscriber_id) & (VideoLike.video.in_(video_ids))
                )
                liked_set = {row.video_id for row in liked_query}

                saved_query = VideoSave.select(VideoSave.video).where(
                    (VideoSave.subscriber == subscriber_id) & (VideoSave.video.in_(video_ids))
                )
                saved_set = {row.video_id for row in saved_query}

                watch_query = WatchHistory.select().where(
                    (WatchHistory.subscriber == subscriber_id) & (WatchHistory.video.in_(video_ids))
                )
                for w in watch_query:
                    watch_map[w.video_id] = {
                        "last_position_seconds": w.last_position_seconds,
                        "completion_percentage": round(w.completion_percentage, 2) if w.completion_percentage is not None else 0.0
                    }

            # Batch likes count for returned videos
            likes_count_query = (
                VideoLike.select(VideoLike.video, fn.COUNT(VideoLike.id).alias("l_count"))
                .where(VideoLike.video.in_(video_ids))
                .group_by(VideoLike.video)
            )
            likes_map = {row.video_id: row.l_count for row in likes_count_query}

            items = []
            for v in paginated_videos:
                order_val = getattr(v.playlistvideo, 'order', 0)
                items.append({
                    "video": v,
                    "order": order_val,
                    "likes": likes_map.get(v.id, 0),
                    "is_liked": v.id in liked_set,
                    "is_saved": v.id in saved_set,
                    "watch_progress": watch_map.get(v.id)
                })

            return items, total
        except PeeweeException as e:
            logger.error(f"Error fetching mobile playlist videos for playlist {playlist.id}: {str(e)}")
            raise e
