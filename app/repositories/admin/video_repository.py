import logging
from datetime import datetime, timezone

from peewee import PeeweeException, fn

from app.models.tenant import Tenant
from app.models.video import Video

logger = logging.getLogger(__name__)


class VideoRepository:
    """
    Data access layer for performing CRUD operations and advanced queries on Video Peewee entities.
    Scoping is enforced by Tenant.
    """

    def create_video(
        self, video_data: dict, tenant_id: int, created_by: int | None = None
    ) -> Video:
        """
        Commits a new Video record into the database with initial status 'pending' linked to tenant_id.
        """
        return Video.create(tenant=tenant_id, created_by=created_by, **video_data)

    def get_video_by_id(self, video_id: int, tenant_id: int) -> Video | None:
        """
        Fetches a video record by integer primary key ID ensuring ownership authorization (tenant_id).
        """
        return Video.get_or_none((Video.id == video_id) & (Video.tenant == tenant_id))

    def get_video_by_bunny_id(self, bunny_video_id: str) -> Video | None:
        """
        Fetches a video record by string Bunny GUID (bunny_video_id) for webhook event processing.
        """
        return Video.get_or_none(Video.bunny_video_id == bunny_video_id)

    def get_all_videos_by_user(
        self,
        tenant_id: int,
        status: str | None = None,
        category: str | None = None,
        search: str | None = None,
        sort: str | None = "newest",
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Fetches a paginated, filtered, and sorted list of video records owned by the tenant.
        """
        query = Video.select().where(Video.tenant == tenant_id)

        if status:
            clean_status = status.lower().strip()
            if clean_status == "draft":
                query = query.where(fn.LOWER(Video.status) == "draft")
            elif clean_status == "processing":
                query = query.where(
                    fn.LOWER(Video.status).in_(
                        ["processing", "pending", "encoding", "upload_finished"]
                    )
                )
            elif clean_status == "published":
                query = query.where(fn.LOWER(Video.status) == "published")
            elif clean_status == "scheduled":
                query = query.where(fn.LOWER(Video.status) == "scheduled")
            else:
                query = query.where(fn.LOWER(Video.status) == clean_status)

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
        elif sort == "popularity":
            query = query.order_by(Video.popularity_score.desc(), Video.created_at.desc())
        elif sort == "title":
            query = query.order_by(Video.title.asc())
        else:  # default newest
            query = query.order_by(Video.created_at.desc())

        total = query.count()
        items = list(query.paginate(page, limit))
        return items, total

    def update_video_metadata(
        self, video_id: int, tenant_id: int, update_data: dict
    ) -> Video | None:
        """
        Updates textual fields (title, description, category, tags) of a video asset in DB.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return None
        for k, v in update_data.items():
            if v is not None:
                setattr(video, k, v)
        video.updated_at = datetime.now(timezone.utc)
        video.save()
        return video

    def update_video_status(
        self,
        bunny_video_id: str,
        status: str,
        encode_progress: int,
        is_playable: bool,
        captions_data: list | None = None,
        available_resolutions: list | None = None,
        duration: str | None = None,
    ) -> Video | None:
        """
        Updates state machine fields (status, encode_progress, is_playable, captions_data, available_resolutions, duration, published_at) of a video record in DB.
        """
        video = self.get_video_by_bunny_id(bunny_video_id)
        if not video:
            return None
        video.status = status
        video.encode_progress = encode_progress
        video.is_playable = is_playable
        if captions_data is not None:
            video.captions_data = captions_data
        if available_resolutions is not None:
            video.available_resolutions = available_resolutions
        if duration:
            video.duration = duration
        if status == "published" and not video.published_at:
            video.published_at = datetime.now(timezone.utc)
        video.updated_at = datetime.now(timezone.utc)
        video.save()
        return video

    def publish_video(self, video_id: int, tenant_id: int) -> Video | None:
        """
        Publishes a video asset immediately, setting status = 'published' and recording ISO UTC timestamp.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return None
        video.status = "published"
        video.publish_intent = "publish"
        video.published_at = datetime.now(timezone.utc)
        video.scheduled_at = None
        video.updated_at = datetime.now(timezone.utc)
        video.save()
        return video

    def unpublish_video(self, video_id: int, tenant_id: int) -> Video | None:
        """
        Unpublishes a video asset, reverting status = 'draft', publish_intent = 'draft', and clearing published_at.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return None
        video.status = "draft"
        video.publish_intent = "draft"
        video.published_at = None
        video.scheduled_at = None
        video.updated_at = datetime.now(timezone.utc)
        video.save()
        return video

    def schedule_video(
        self, video_id: int, tenant_id: int, scheduled_at_dt: datetime
    ) -> Video | None:
        """
        Schedules a video asset for future publication, setting status = 'scheduled' and target datetime.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return None
        video.status = "scheduled"
        video.publish_intent = "schedule"
        video.scheduled_at = scheduled_at_dt
        video.updated_at = datetime.now(timezone.utc)
        video.save()
        return video

    def publish_due_scheduled_videos(self) -> int:
        """
        Bulk updates all videos where status = 'scheduled' and scheduled_at <= datetime.now().
        Flips status = 'published', published_at = scheduled_at, and clears scheduled_at = None.
        """
        try:
            now = datetime.now(timezone.utc)
            active_tenants = Tenant.select(Tenant.id).where(Tenant.is_active == True)
            count = (
                Video.update(
                    status="published",
                    published_at=Video.scheduled_at,
                    scheduled_at=None,
                )
                .where(
                    (Video.status == "scheduled")
                    & (Video.scheduled_at.is_null(False))
                    & (Video.scheduled_at <= now)
                    & (Video.tenant.in_(active_tenants))
                )
                .execute()
            )
            return count
        except PeeweeException as e:
            logger.error("Error publishing due scheduled videos: %s", e)
            return 0

    def swap_main_thumbnail(
        self, video_id: int, tenant_id: int, new_main_url: str
    ) -> Video | None:
        """
        Updates main_thumbnail_url and pushes the previous main URL into alt_thumbnail_urls list.
        """
        video = self.get_video_by_id(video_id, tenant_id)
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

    def delete_alt_thumbnail_url(
        self, video_id: int, tenant_id: int, target_url: str
    ) -> Video | None:
        """
        Removes a target thumbnail URL entry from alt_thumbnail_urls array in DB.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return None
        alts = list(video.alt_thumbnail_urls or [])
        if target_url in alts:
            alts.remove(target_url)
            video.alt_thumbnail_urls = alts
            video.save()
        return video

    def update_thumbnail_url(
        self, video_id: int, tenant_id: int, slot: int, new_url: str
    ) -> Video | None:
        """
        Updates main_thumbnail_url (slot 0) or alt_thumbnail_urls list (slot 1 or 2) in DB.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return None
        if slot == 0:
            video.main_thumbnail_url = new_url
        else:
            alts = list(video.alt_thumbnail_urls or [])
            idx = slot - 1
            if idx < len(alts):
                alts[idx] = new_url
            else:
                alts.append(new_url)
            video.alt_thumbnail_urls = alts
        video.save()
        return video

    def delete_video(self, video_id: int, tenant_id: int) -> bool:
        """
        Deletes a video record from DB and cascades playlist association cleanup.
        """
        video = self.get_video_by_id(video_id, tenant_id)
        if not video:
            return False
        video.delete_instance(recursive=True)
        return True

    def bulk_delete_videos(self, video_ids: list[int], tenant_id: int) -> list[Video]:
        """
        Fetches and deletes multiple video assets by ID array owned by tenant. Returns deleted Video instances.
        """
        videos = list(
            Video.select().where((Video.id.in_(video_ids)) & (Video.tenant == tenant_id))
        )
        for video in videos:
            video.delete_instance(recursive=True)
        return videos
