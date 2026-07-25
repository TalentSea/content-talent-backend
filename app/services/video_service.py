import logging
import math
import time
from datetime import datetime, timezone
from typing import Optional, List
from zoneinfo import ZoneInfo
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.video_repository import VideoRepository
from app.schemas.video_schemas import (
    VideoInitiateRequest,
    VideoInitiateResponse,
    VideoResponse,
    VideoListItemResponse,
    VideoUpdateRequest,
    VideoUpdateResponse,
    SelectMainThumbnailRequest,
    DeleteThumbnailRequest,
    VideoPublishResponse,
    VideoScheduleRequest,
    VideoScheduleResponse,
    BulkDeleteVideosRequest,
    BunnyWebhookPayload
)
from app.schemas.common_schemas import PaginatedResponse, ActionSuccessResponse
from app.utils.bunny_client import (
    create_bunny_video,
    get_bunny_video_status,
    delete_bunny_video,
    upload_bunny_stream_thumbnail,
    upload_bunny_storage_file,
    delete_bunny_storage_file
)
from app.utils.bunny_signature import generate_tus_signature, generate_signed_playback_url

logger = logging.getLogger(__name__)

class BunnyVideoState:
    """Canonical data container for resolved video state machine values."""
    def __init__(self, db_status: str, progress: int, is_playable: bool):
        self.db_status = db_status
        self.progress = progress
        self.is_playable = is_playable

# Centralized status mapping dictionary (Single Source of Truth)
BUNNY_STATUS_MAP = {
    0: ("PENDING", 0, False),
    1: ("PROCESSING", 25, False),
    2: ("ENCODING", 65, False),
    3: ("READY", 100, True),
    4: ("PLAYABLE", 80, True),
    5: ("FAILED", 0, False),
    6: ("PENDING", 0, False),
    7: ("UPLOAD_FINISHED", 0, False),
    8: ("UPLOAD_FAILED", 0, False),
    9: ("READY", 100, True),
    10: ("READY", 100, True),
}

def resolve_bunny_status(status_code: int, live_progress: Optional[int] = None) -> Optional[BunnyVideoState]:
    """
    Centralized status code state resolver used by both Webhooks and Live API status polling.
    Eliminates code duplication across video status synchronization.
    """
    if status_code not in BUNNY_STATUS_MAP:
        return None
    db_status, default_prog, is_playable = BUNNY_STATUS_MAP[status_code]
    progress = live_progress if live_progress is not None else default_prog
    return BunnyVideoState(db_status, progress, is_playable)


class VideoService:
    """
    Business logic and cloud orchestration layer for Video operations (Peewee ORM).
    """

    def __init__(self):
        self.repo = VideoRepository()

    def _to_video_response(self, video) -> VideoResponse:
        """
        Maps a Video Peewee ORM instance to a canonical VideoResponse DTO.
        """
        settings = get_settings()
        playback_url = None
        if video.is_playable or video.status in ("READY", "PLAYABLE", "published"):
            playback_url = generate_signed_playback_url(
                settings.BUNNY_PULL_ZONE_URL,
                video.bunny_video_id,
                settings.BUNNY_STREAM_TOKEN_KEY
            )

        return VideoResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            category=video.category,
            tags=list(video.tags or []),
            status=video.status,
            encode_progress=video.encode_progress,
            is_playable=video.is_playable,
            views=video.views or 0,
            duration=video.duration,
            playback_url=playback_url,
            main_thumbnail_url=video.main_thumbnail_url,
            alt_thumbnail_urls=list(video.alt_thumbnail_urls or []),
            published_at=video.published_at,
            scheduled_at=video.scheduled_at,
            created_at=video.created_at
        )

    def _to_video_list_item_response(self, video) -> VideoListItemResponse:
        """
        Maps a Video Peewee ORM instance to a lightweight VideoListItemResponse DTO matching spec doc API 3.
        """
        return VideoListItemResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            category=video.category,
            tags=list(video.tags or []),
            status=video.status,
            encode_progress=video.encode_progress,
            is_playable=video.is_playable,
            views=video.views or 0,
            duration=video.duration,
            main_thumbnail_url=video.main_thumbnail_url,
            published_at=video.published_at,
            scheduled_at=video.scheduled_at,
            created_at=video.created_at
        )

    def _to_video_update_response(self, video) -> VideoUpdateResponse:
        """
        Maps a Video Peewee ORM instance to a pure text-only VideoUpdateResponse DTO matching spec doc API 5.
        """
        return VideoUpdateResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            category=video.category,
            tags=list(video.tags or []),
            status=video.status
        )

    def initiate_video_upload(self, user_id: int, payload: VideoInitiateRequest) -> VideoInitiateResponse:
        """
        Creates video container on Bunny Stream, generates TUS upload signature, and commits initial DB record.
        """
        settings = get_settings()
        library_id = str(settings.BUNNY_STREAM_LIBRARY_ID)
        api_key = settings.BUNNY_STREAM_API_KEY

        bunny_response = create_bunny_video(payload.title)
        bunny_video_id = bunny_response.get("guid")

        if not bunny_video_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reserve video container on Bunny Stream"
            )

        expiration_timestamp = int(time.time()) + 86400
        signature = generate_tus_signature(
            library_id=library_id,
            api_key=api_key,
            expiration_time=expiration_timestamp,
            video_id=bunny_video_id
        )

        pull_zone = settings.BUNNY_PULL_ZONE_URL.rstrip("/")
        main_thumbnail_url = f"{pull_zone}/{bunny_video_id}/thumbnail.jpg"
        alt_thumbnail_urls = [
            f"{pull_zone}/{bunny_video_id}/thumb_2.jpg",
            f"{pull_zone}/{bunny_video_id}/thumb_3.jpg"
        ]

        video_record_data = {
            "bunny_video_id": bunny_video_id,
            "title": payload.title,
            "description": payload.description,
            "category": payload.category,
            "tags": payload.tags or [],
            "status": "PENDING",
            "encode_progress": 0,
            "is_playable": False,
            "main_thumbnail_url": main_thumbnail_url,
            "alt_thumbnail_urls": alt_thumbnail_urls
        }

        created_video = self.repo.create_video(video_record_data, user_id)

        return VideoInitiateResponse(
            id=created_video.id,
            bunny_video_id=bunny_video_id,
            bunny_library_id=library_id,
            status=created_video.status,
            signature=signature,
            expiration_time=expiration_timestamp
        )

    def handle_bunny_webhook(self, payload: BunnyWebhookPayload) -> ActionSuccessResponse:
        """
        Processes status code state machine (0 to 10) from Bunny Stream webhook events using centralized resolver.
        """
        status_code = payload.Status
        state = resolve_bunny_status(status_code)

        if not state:
            logger.warning(f"Unrecognized Bunny webhook status code {status_code} for video {payload.VideoGuid}")
            return ActionSuccessResponse(status="success")

        caption_url = None
        if status_code in (9, 10):
            pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
            caption_url = f"{pull_zone}/{payload.VideoGuid}/captions/en.vtt"

        self.repo.update_video_status(
            bunny_video_id=payload.VideoGuid,
            status=state.db_status,
            encode_progress=state.progress,
            is_playable=state.is_playable,
            caption_url=caption_url
        )

        return ActionSuccessResponse(status="success")

    def list_user_videos(
        self,
        user_id: int,
        status_filter: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = "newest",
        date_from_str: Optional[str] = None,
        date_to_str: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> PaginatedResponse[VideoListItemResponse]:
        """
        Retrieves a paginated, filterable list of videos owned by creator.
        """
        date_from = None
        date_to = None
        if date_from_str:
            try:
                date_from = datetime.fromisoformat(date_from_str)
            except ValueError:
                pass
        if date_to_str:
            try:
                date_to = datetime.fromisoformat(date_to_str)
            except ValueError:
                pass

        videos, total = self.repo.get_all_videos_by_user(
            user_id=user_id,
            status=status_filter,
            category=category,
            search=search,
            sort=sort,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit
        )

        items = [self._to_video_list_item_response(v) for v in videos]
        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items
        )

    def get_video_details(self, user_id: int, video_id: int) -> VideoResponse:
        """
        Retrieves detailed metadata for a single video. Syncs live encoding status from Bunny Stream if ENCODING.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        if video.status in ("ENCODING", "PROCESSING"):
            try:
                status_data = get_bunny_video_status(video.bunny_video_id)
                if status_data and "status" in status_data:
                    code = status_data.get("status")
                    prog = status_data.get("encodeProgress")
                    state = resolve_bunny_status(code, live_progress=prog)
                    if state:
                        video = self.repo.update_video_status(
                            bunny_video_id=video.bunny_video_id,
                            status=state.db_status,
                            encode_progress=state.progress,
                            is_playable=state.is_playable
                        ) or video
            except Exception as e:
                logger.warning(f"Live status sync skipped for video {video.bunny_video_id}: {str(e)}")

        return self._to_video_response(video)

    def update_video_metadata(self, user_id: int, video_id: int, payload: VideoUpdateRequest) -> VideoUpdateResponse:
        """
        Validates ownership and applies partial textual metadata updates (title, description, category, tags) in DB.
        """
        update_data = payload.model_dump(exclude_unset=True)
        video = self.repo.update_video_metadata(video_id, user_id, update_data)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")
        return self._to_video_update_response(video)

    def upload_thumbnail_image(self, user_id: int, video_id: int, slot: int, file: UploadFile) -> ActionSuccessResponse:
        """
        Uploads thumbnail binary image for slot 0 (Bunny Stream API) or slot 1/2 (Bunny Storage API) via server proxy.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        if slot not in (0, 1, 2):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thumbnail slot must be 0, 1, or 2")

        allowed_mime_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        content_type = (file.content_type or "").lower()
        if content_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{file.content_type}'. Only JPEG, PNG, and WebP images are allowed."
            )

        file_bytes = file.file.read()
        ext = "png" if "png" in content_type else ("webp" if "webp" in content_type else "jpg")
        filename = f"thumb_{slot + 1}.{ext}" if slot > 0 else "thumbnail.jpg"

        if slot == 0:
            upload_bunny_stream_thumbnail(video.bunny_video_id, file_bytes, content_type)
        else:
            file_path = f"{video.bunny_video_id}/{filename}"
            upload_bunny_storage_file(file_path, file_bytes, content_type)

        return ActionSuccessResponse(status="success")

    def select_main_thumbnail(self, user_id: int, video_id: int, payload: SelectMainThumbnailRequest) -> ActionSuccessResponse:
        """
        Executes thumbnail swapping logic between main cover and alt thumbnails in DB.
        """
        video = self.repo.swap_main_thumbnail(video_id, user_id, payload.selected_main_thumbnail)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")
        return ActionSuccessResponse(status="success")

    def delete_alternative_thumbnail(self, user_id: int, video_id: int, payload: DeleteThumbnailRequest) -> ActionSuccessResponse:
        """
        Issues HTTP DELETE to Bunny Storage API to remove physical cloud image and updates DB list.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        target_url = payload.thumbnail_url
        file_path = f"{video.bunny_video_id}/{target_url.split('/')[-1]}"
        try:
            delete_bunny_storage_file(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete Bunny Storage thumbnail file {file_path}: {str(e)}")

        self.repo.delete_alt_thumbnail_url(video_id, user_id, target_url)
        return ActionSuccessResponse(status="success")

    def delete_video_asset(self, user_id: int, video_id: int) -> ActionSuccessResponse:
        """
        Issues HTTP DELETE to Bunny Stream API to remove cloud video container and drops video record from DB.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        try:
            delete_bunny_video(video.bunny_video_id)
        except Exception as e:
            logger.warning(f"Failed to delete Bunny Stream container for video {video.bunny_video_id}: {str(e)}")

        for url in (video.alt_thumbnail_urls or []):
            try:
                file_path = f"{video.bunny_video_id}/{url.split('/')[-1]}"
                delete_bunny_storage_file(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete Bunny Storage thumbnail {url}: {str(e)}")

        self.repo.delete_video(video_id, user_id)
        return ActionSuccessResponse(status="success")

    def bulk_delete_videos(self, user_id: int, payload: BulkDeleteVideosRequest) -> ActionSuccessResponse:
        """
        Bulk deletes multiple video assets by ID array owned by creator.
        """
        deleted_videos = self.repo.bulk_delete_videos(payload.video_ids, user_id)
        for video in deleted_videos:
            try:
                delete_bunny_video(video.bunny_video_id)
            except Exception as e:
                logger.warning(f"Failed to bulk delete Bunny container {video.bunny_video_id}: {str(e)}")

        return ActionSuccessResponse(status="success")

    def publish_video_immediately(self, user_id: int, video_id: int) -> VideoPublishResponse:
        """
        Publishes a video asset immediately, updating state to 'published' and recording published_at timestamp.
        """
        video = self.repo.publish_video(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        return VideoPublishResponse(
            id=video.id,
            status=video.status,
            published_at=video.published_at
        )

    def schedule_video_publication(self, user_id: int, video_id: int, payload: VideoScheduleRequest) -> VideoScheduleResponse:
        """
        Schedules a video asset for future publication, parsing local date/time/timezone into UTC datetime.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        try:
            local_tz = ZoneInfo(payload.timezone)
            local_dt_str = f"{payload.date} {payload.time}"
            local_dt = datetime.strptime(local_dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
            utc_dt = local_dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date, time, or timezone specification: {str(e)}"
            )

        updated_video = self.repo.schedule_video(video_id, user_id, utc_dt)
        return VideoScheduleResponse(
            id=updated_video.id,
            status=updated_video.status,
            scheduled_at=updated_video.scheduled_at
        )
