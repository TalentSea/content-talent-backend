from typing import List, Tuple, Optional
from datetime import datetime
from peewee import fn
from app.models.playlist import Playlist, PlaylistVideo
from app.models.video import Video

class PlaylistRepository:
    """
    Data access layer for performing CRUD operations on Playlist Peewee entities.
    """

    def create_playlist(self, playlist_data: dict, user_id: int) -> Playlist:
        """
        Commits a new Playlist record into DB and attaches initial video IDs in junction table.
        """
        data = dict(playlist_data)
        video_ids = data.pop("video_ids", []) or []
        playlist = Playlist.create(user=user_id, **data)

        for order, vid_id in enumerate(video_ids):
            if Video.select().where((Video.id == vid_id) & (Video.user == user_id)).exists():
                PlaylistVideo.create(playlist=playlist, video=vid_id, order=order)

        return playlist

    def get_playlist_by_id(self, playlist_id: int, user_id: int) -> Optional[Playlist]:
        """
        Retrieves a playlist by primary key ID ensuring ownership authorization check.
        """
        return Playlist.get_or_none((Playlist.id == playlist_id) & (Playlist.user == user_id))

    def get_playlist_video_count(self, playlist: Playlist) -> int:
        """
        Returns total count of attached videos inside a playlist.
        """
        return PlaylistVideo.select().where(PlaylistVideo.playlist == playlist).count()

    def get_playlist_videos(
        self,
        playlist_id: int,
        user_id: int,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[Optional[Playlist], List[Tuple[Video, int, datetime]], int]:
        """
        Retrieves attached videos for a playlist with order and added_at metadata, supporting title search and pagination.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return None, [], 0

        query = (Video.select(Video, PlaylistVideo.order, PlaylistVideo.added_at)
                 .join(PlaylistVideo)
                 .where(PlaylistVideo.playlist == playlist))

        if search:
            query = query.where(Video.title.contains(search))

        query = query.order_by(PlaylistVideo.order.asc())
        total = query.count()
        
        # Paginate results
        paginated_query = query.paginate(page, limit)
        results = []
        for v in paginated_query:
            order_val = getattr(v.playlistvideo, 'order', 0)
            added_at_val = getattr(v.playlistvideo, 'added_at', datetime.now())
            results.append((v, order_val, added_at_val))

        return playlist, results, total

    def get_all_playlists_by_user(
        self,
        user_id: int,
        search: Optional[str] = None,
        sort: Optional[str] = "newest",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Tuple[Playlist, int]], int]:
        """
        Fetches a paginated, filtered, and sorted list of creator playlists along with total count.
        """
        query = Playlist.select().where(Playlist.user == user_id)

        if search:
            query = query.where(Playlist.name.contains(search))

        if sort == "oldest":
            query = query.order_by(Playlist.created_at.asc())
        elif sort == "title":
            query = query.order_by(Playlist.name.asc())
        else:  # default newest
            query = query.order_by(Playlist.created_at.desc())

        total = query.count()
        playlists = list(query.paginate(page, limit))

        results = []
        for p in playlists:
            v_count = self.get_playlist_video_count(p)
            results.append((p, v_count))

        return results, total

    def update_playlist(self, playlist_id: int, user_id: int, update_data: dict) -> Optional[Playlist]:
        """
        Updates playlist textual metadata (name, description) and records updated_at timestamp.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return None

        for k, v in update_data.items():
            if v is not None:
                setattr(playlist, k, v)
        playlist.updated_at = datetime.now()
        playlist.save()
        return playlist

    def add_videos_to_playlist(self, playlist_id: int, user_id: int, video_ids: List[int]) -> Optional[Playlist]:
        """
        Adds an array of video IDs to the specified playlist if owned by creator.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return None

        max_order = (PlaylistVideo.select(fn.MAX(PlaylistVideo.order))
                     .where(PlaylistVideo.playlist == playlist)
                     .scalar() or 0)

        curr_order = max_order + 1 if max_order > 0 else 0
        for vid_id in video_ids:
            exists = Video.select().where((Video.id == vid_id) & (Video.user == user_id)).exists()
            link_exists = PlaylistVideo.select().where((PlaylistVideo.playlist == playlist) & (PlaylistVideo.video == vid_id)).exists()
            if exists and not link_exists:
                PlaylistVideo.create(playlist=playlist, video=vid_id, order=curr_order)
                curr_order += 1

        playlist.updated_at = datetime.now()
        playlist.save()
        return playlist

    def remove_video_from_playlist(self, playlist_id: int, user_id: int, video_id: int) -> bool:
        """
        Removes a single video link from a playlist.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return False

        deleted = PlaylistVideo.delete().where((PlaylistVideo.playlist == playlist) & (PlaylistVideo.video == video_id)).execute()
        if deleted > 0:
            playlist.updated_at = datetime.now()
            playlist.save()
            return True
        return False

    def bulk_remove_videos_from_playlist(self, playlist_id: int, user_id: int, video_ids: List[int]) -> bool:
        """
        Bulk removes an array of video IDs from a playlist.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return False

        deleted = PlaylistVideo.delete().where((PlaylistVideo.playlist == playlist) & (PlaylistVideo.video.in_(video_ids))).execute()
        if deleted > 0:
            playlist.updated_at = datetime.now()
            playlist.save()
            return True
        return False

    def reorder_playlist_videos(self, playlist_id: int, user_id: int, video_orders: List[dict]) -> bool:
        """
        Persists updated sequence positions (order) of videos inside a playlist.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return False

        for vo in video_orders:
            vid_id = vo.get("video_id")
            order_val = vo.get("order")
            if vid_id is not None and order_val is not None:
                PlaylistVideo.update(order=order_val).where((PlaylistVideo.playlist == playlist) & (PlaylistVideo.video == vid_id)).execute()

        playlist.updated_at = datetime.now()
        playlist.save()
        return True

    def delete_playlist(self, playlist_id: int, user_id: int) -> bool:
        """
        Deletes a playlist record from DB and clears junction table links.
        """
        playlist = self.get_playlist_by_id(playlist_id, user_id)
        if not playlist:
            return False
        playlist.delete_instance(recursive=True)
        return True

    def get_available_videos_for_playlist(
        self,
        playlist_id: int,
        user_id: int,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort: Optional[str] = "newest",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Video], int]:
        """
        Executes query returning paginated, filtered, and sorted list of creator videos NOT attached to the specified playlist.
        """
        attached_subquery = PlaylistVideo.select(PlaylistVideo.video_id).where(PlaylistVideo.playlist_id == playlist_id)
        query = Video.select().where((Video.user == user_id) & (Video.id.not_in(attached_subquery)))

        if search:
            query = query.where(Video.title.contains(search))

        if category:
            query = query.where(fn.LOWER(Video.category) == category.lower())

        if sort == "oldest":
            query = query.order_by(Video.created_at.asc())
        elif sort == "views":
            query = query.order_by(Video.views.desc(), Video.created_at.desc())
        elif sort == "title":
            query = query.order_by(Video.title.asc())
        else:  # default newest
            query = query.order_by(Video.created_at.desc())

        total = query.count()
        videos = list(query.paginate(page, limit))
        return videos, total
