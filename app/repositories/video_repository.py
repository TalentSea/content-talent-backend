from typing import Optional, List, Tuple
from datetime import datetime
from peewee import fn
from app.models.video import Video

class VideoRepository:
    """
    Data access layer for performing CRUD operations and advanced queries on Video Peewee entities.
    """

    def create_video(self, video_data: dict, user_id: int) -> Video:
        """
        Commits a new Video record into the database with initial status 'PENDING' linked to user_id.
        """
        return Video.create(user=user_id, **video_data)

    def get_video_by_id(self, video_id: int, user_id: int) -> Optional[Video]:
        """
        Fetches a video record by integer primary key ID ensuring ownership authorization (user_id).
        """
        return Video.get_or_none((Video.id == video_id) & (Video.user == user_id))

    def get_video_by_bunny_id(self, bunny_video_id: str) -> Optional[Video]:
        """
        Fetches a video record by string Bunny GUID (bunny_video_id) for webhook event processing.
        """
        return Video.get_or_none(Video.bunny_video_id == bunny_video_id)

    def get_all_videos_by_user(
        self,
        user_id: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = "newest",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Video], int]:
        """
        Fetches a paginated, filtered, and sorted list of video records owned by the creator.
        """
        query = Video.select().where(Video.user == user_id)

        if status:
            query = query.where(fn.LOWER(Video.status) == status.lower())

        if category:
            query = query.where(fn.LOWER(Video.category) == category.lower())

        if search:
            query = query.where(Video.title.contains(search))

        if date_from:
            query = query.where(Video.created_at >= date_from)

        if date_to:
            query = query.where(Video.created_at <= date_to)

        # Apply sorting logic
        if sort == "oldest":
            query = query.order_by(Video.created_at.asc())
        elif sort == "views":
            query = query.order_by(Video.views.desc(), Video.created_at.desc())
        elif sort == "title":
            query = query.order_by(Video.title.asc())
        else:  # default newest
            query = query.order_by(Video.created_at.desc())

        total = query.count()
        items = list(query.paginate(page, limit))
        return items, total

    def update_video_metadata(self, video_id: int, user_id: int, update_data: dict) -> Optional[Video]:
        """
        Updates textual fields (title, description, category, tags) of a video asset in DB.
        """
        video = self.get_video_by_id(video_id, user_id)
        if not video:
            return None
        for k, v in update_data.items():
            if v is not None:
                setattr(video, k, v)
        video.save()
        return video

    def update_video_status(
        self,
        bunny_video_id: str,
        status: str,
        encode_progress: int,
        is_playable: bool,
        caption_url: Optional[str] = None
    ) -> Optional[Video]:
        """
        Updates state machine fields (status, encode_progress, is_playable) of a video record in DB.
        """
        video = self.get_video_by_bunny_id(bunny_video_id)
        if not video:
            return None
        video.status = status
        video.encode_progress = encode_progress
        video.is_playable = is_playable
        if caption_url:
            video.caption_url = caption_url
        video.save()
        return video

    def publish_video(self, video_id: int, user_id: int) -> Optional[Video]:
        """
        Publishes a video asset immediately, setting status = 'published' and recording ISO UTC timestamp.
        """
        video = self.get_video_by_id(video_id, user_id)
        if not video:
            return None
        video.status = "published"
        video.published_at = datetime.utcnow()
        video.scheduled_at = None
        video.save()
        return video

    def schedule_video(self, video_id: int, user_id: int, scheduled_at_dt: datetime) -> Optional[Video]:
        """
        Schedules a video asset for future publication, setting status = 'scheduled' and target UTC datetime.
        """
        video = self.get_video_by_id(video_id, user_id)
        if not video:
            return None
        video.status = "scheduled"
        video.scheduled_at = scheduled_at_dt
        video.save()
        return video

    def swap_main_thumbnail(self, video_id: int, user_id: int, new_main_url: str) -> Optional[Video]:
        """
        Updates main_thumbnail_url and pushes the previous main URL into alt_thumbnail_urls list.
        """
        video = self.get_video_by_id(video_id, user_id)
        if not video:
            return None
        old_main = video.main_thumbnail_url
        video.main_thumbnail_url = new_main_url
        alts = list(video.alt_thumbnail_urls or [])
        if new_main_url in alts:
            alts.remove(new_main_url)
        if old_main and old_main not in alts:
            alts.append(old_main)
        video.alt_thumbnail_urls = alts
        video.save()
        return video

    def delete_alt_thumbnail_url(self, video_id: int, user_id: int, target_url: str) -> Optional[Video]:
        """
        Removes a target thumbnail URL entry from alt_thumbnail_urls array in DB.
        """
        video = self.get_video_by_id(video_id, user_id)
        if not video:
            return None
        alts = list(video.alt_thumbnail_urls or [])
        if target_url in alts:
            alts.remove(target_url)
            video.alt_thumbnail_urls = alts
            video.save()
        return video

    def delete_video(self, video_id: int, user_id: int) -> bool:
        """
        Deletes a video record from DB and cascades playlist association cleanup.
        """
        video = self.get_video_by_id(video_id, user_id)
        if not video:
            return False
        video.delete_instance(recursive=True)
        return True

    def bulk_delete_videos(self, video_ids: List[int], user_id: int) -> List[Video]:
        """
        Fetches and deletes multiple video assets by ID array owned by creator. Returns deleted Video instances.
        """
        videos = list(Video.select().where((Video.id.in_(video_ids)) & (Video.user == user_id)))
        for video in videos:
            video.delete_instance(recursive=True)
        return videos
