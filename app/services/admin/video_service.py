import logging
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.models.video import VideoLike
from app.repositories.admin.video_repository import VideoRepository
from app.schemas.shared.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.schemas.admin.video_schemas import (
    BulkDeleteVideosRequest,
    BunnyWebhookPayload,
    DeleteThumbnailRequest,
    DownloadUrlItem,
    SelectMainThumbnailRequest,
    VideoInitiateRequest,
    VideoInitiateResponse,
    VideoListItemResponse,
    VideoPublishResponse,
    VideoResponse,
    VideoScheduleRequest,
    VideoScheduleResponse,
    VideoUpdateRequest,
    VideoUpdateResponse,
)
from app.utils.bunny_client import (
    create_bunny_video,
    delete_bunny_storage_file,
    delete_bunny_video,
    get_bunny_video_status,
)
from app.utils.bunny_signature import (
    generate_signed_mp4_url,
    generate_signed_playback_url,
    generate_tus_signature,
)
from app.utils.image_uploader import validate_and_upload_image

logger = logging.getLogger("uvicorn.error")


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


def resolve_bunny_status(
    status_code: int, live_progress: int | None = None
) -> BunnyVideoState | None:
    """
    Centralized status code state resolver used by both Webhooks and Live API status polling.
    Eliminates code duplication across video status synchronization.
    """
    if status_code not in BUNNY_STATUS_MAP:
        return None
    db_status, default_prog, is_playable = BUNNY_STATUS_MAP[status_code]
    progress = live_progress if live_progress is not None else default_prog
    return BunnyVideoState(db_status, progress, is_playable)


def format_duration(seconds: int | None) -> str | None:
    """Formats integer seconds into MM:SS or HH:MM:SS string."""
    if not seconds or seconds <= 0:
        return None
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def normalize_tags(tags: list[str] | None) -> list[str]:
    """
    Cleans and splits space-separated tags into individual hashtag items.
    Example: ['#GodOfWar #Marvel'] -> ['#GodOfWar', '#Marvel']
    """
    if not tags:
        return []
    clean_tags = []
    for tag in tags:
        if isinstance(tag, str):
            words = tag.strip().split()
            for word in words:
                word_clean = word.strip()
                if word_clean and word_clean not in clean_tags:
                    clean_tags.append(word_clean)
    return clean_tags


class VideoService:
    """
    Business logic and cloud orchestration layer for Video operations (Peewee ORM).
    """

    def __init__(self):
        self.repo = VideoRepository()

    def _generate_download_urls(self, video) -> list[DownloadUrlItem]:
        """
        Generates presigned time-bound MP4 download URLs for all available resolutions (play_<resolution>.mp4).
        """
        if not video.is_playable or not video.available_resolutions:
            return []
        settings = get_settings()
        pull_zone = settings.BUNNY_PULL_ZONE_URL
        token_key = settings.BUNNY_STREAM_TOKEN_KEY
        res_list = list(video.available_resolutions or [])
        download_items = []
        for res in res_list:
            clean_res = str(res).strip()
            if not clean_res:
                continue
            if not clean_res.endswith("p"):
                clean_res = f"{clean_res}p"
            label = (
                f"{clean_res} HD"
                if clean_res in ("720p", "1080p", "1440p", "2160p")
                else f"{clean_res} SD"
            )
            url = generate_signed_mp4_url(
                bunny_pull_zone_url=pull_zone,
                bunny_video_id=video.bunny_video_id,
                resolution=clean_res,
                token_security_key=token_key,
            )
            download_items.append(
                DownloadUrlItem(resolution=clean_res, label=label, url=url)
            )
        return download_items

    def _get_likes_count(self, video_id: int) -> int:
        """Helper returning total likes for a video asset."""
        return VideoLike.select().where(VideoLike.video == video_id).count()

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
                settings.BUNNY_STREAM_TOKEN_KEY,
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
            likes=self._get_likes_count(video.id),
            duration=video.duration,
            playback_url=playback_url,
            main_thumbnail_url=video.main_thumbnail_url,
            alt_thumbnail_urls=list(video.alt_thumbnail_urls or []),
            captions_data=list(video.captions_data or []),
            download_urls=self._generate_download_urls(video),
            published_at=video.published_at,
            scheduled_at=video.scheduled_at,
            created_at=video.created_at,
        )

    def _to_video_list_item_response(self, video) -> VideoListItemResponse:
        """
        Maps a Video Peewee ORM instance to a lightweight VideoListItemResponse DTO matching spec doc API 3.
        """
        return VideoListItemResponse(
            id=video.id,
            title=video.title,
            category=video.category,
            status=video.status,
            encode_progress=video.encode_progress,
            is_playable=video.is_playable,
            views=video.views or 0,
            likes=self._get_likes_count(video.id),
            duration=video.duration,
            main_thumbnail_url=video.main_thumbnail_url,
            published_at=video.published_at,
            scheduled_at=video.scheduled_at,
            created_at=video.created_at,
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
            status=video.status,
        )

    def initiate_video_upload(
        self, user_id: int, payload: VideoInitiateRequest
    ) -> VideoInitiateResponse:
        """
        Reserves a video container on Bunny Stream, prepares local database record in PENDING state,
        and generates HMAC SHA256 signature for TUS protocol frontend direct upload.
        """
        settings = get_settings()

        # Step 1: Call Bunny Stream API to create video container
        bunny_res = create_bunny_video(payload.title)
        bunny_video_id = bunny_res.get("guid")
        library_id = settings.BUNNY_STREAM_LIBRARY_ID

        if not bunny_video_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Bunny Stream API failed to return a valid video GUID",
            )

        # Step 2: Compute TUS signature for frontend direct upload
        signature, expiration_timestamp = generate_tus_signature(
            library_id, settings.BUNNY_STREAM_API_KEY, bunny_video_id
        )

        pull_zone = settings.BUNNY_PULL_ZONE_URL.rstrip("/")
        main_thumbnail_url = f"{pull_zone}/{bunny_video_id}/thumb_1.jpg"
        alt_thumbnail_urls = [
            f"{pull_zone}/{bunny_video_id}/thumb_2.jpg",
            f"{pull_zone}/{bunny_video_id}/thumb_3.jpg",
        ]

        # Step 3: Insert initial PENDING video record into database
        video_record_data = {
            "bunny_video_id": bunny_video_id,
            "title": payload.title,
            "description": payload.description,
            "category": payload.category,
            "tags": normalize_tags(payload.tags),
            "status": "PENDING",
            "encode_progress": 0,
            "is_playable": False,
            "main_thumbnail_url": main_thumbnail_url,
            "alt_thumbnail_urls": alt_thumbnail_urls,
        }

        created_video = self.repo.create_video(video_record_data, user_id)

        return VideoInitiateResponse(
            id=created_video.id,
            bunny_video_id=bunny_video_id,
            bunny_library_id=library_id,
            status=created_video.status,
            signature=signature,
            expiration_time=expiration_timestamp,
        )

    def handle_bunny_webhook(
        self, payload: BunnyWebhookPayload
    ) -> ActionSuccessResponse:
        """
        Processes status code state machine (0 to 10) from Bunny Stream webhook events using centralized resolver.
        """
        status_code = payload.Status
        logger.info(
            f"Received Bunny Stream Webhook Event: Status={status_code}, VideoGuid={payload.VideoGuid}"
        )
        state = resolve_bunny_status(status_code)

        if not state:
            logger.warning(
                f"Unrecognized Bunny webhook status code {status_code} for video {payload.VideoGuid}"
            )
            return ActionSuccessResponse(status="success")

        existing_video = self.repo.get_video_by_bunny_id(payload.VideoGuid)
        duration_str = None
        captions_data = None
        available_resolutions = None

        should_fetch_duration = bool(
            existing_video
            and not existing_video.duration
            and status_code in (1, 2, 3, 4, 9, 10)
        )
        should_fetch_captions = bool(
            status_code == 9 and existing_video and not existing_video.captions_data
        )
        should_fetch_resolutions = bool(
            status_code in (3, 4)
            or (
                existing_video
                and not existing_video.available_resolutions
                and status_code in (1, 2, 3, 4, 9, 10)
            )
        )

        if should_fetch_duration or should_fetch_captions or should_fetch_resolutions:
            try:
                status_data = get_bunny_video_status(payload.VideoGuid)
                if status_data:
                    if should_fetch_duration and "length" in status_data:
                        duration_str = format_duration(status_data.get("length"))

                    if "availableResolutions" in status_data:
                        raw_res = status_data.get("availableResolutions")
                        if isinstance(raw_res, str):
                            available_resolutions = [
                                r.strip() for r in raw_res.split(",") if r.strip()
                            ]
                        elif isinstance(raw_res, list):
                            available_resolutions = [
                                str(r).strip() for r in raw_res if str(r).strip()
                            ]

                    if should_fetch_captions:
                        captions_list = status_data.get("captions") or []
                        if captions_list:
                            pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
                            captions_data = []
                            for idx, track in enumerate(captions_list):
                                if isinstance(track, dict) and track.get("srclang"):
                                    srclang = str(track.get("srclang")).strip()
                                    label = str(
                                        track.get("label") or srclang.upper()
                                    ).strip()
                                    captions_data.append(
                                        {
                                            "srclang": srclang,
                                            "label": label,
                                            "is_default": (idx == 0),
                                            "url": f"{pull_zone}/{payload.VideoGuid}/captions/{srclang}.vtt",
                                        }
                                    )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to fetch Bunny Stream status for %s: %s",
                    payload.VideoGuid,
                    e,
                )

        self.repo.update_video_status(
            bunny_video_id=payload.VideoGuid,
            status=state.db_status,
            encode_progress=state.progress,
            is_playable=state.is_playable,
            captions_data=captions_data,
            available_resolutions=available_resolutions,
            duration=duration_str,
        )

        return ActionSuccessResponse(status="success")

    def list_user_videos(
        self,
        user_id: int,
        status_filter: str | None = None,
        category: str | None = None,
        search: str | None = None,
        sort: str | None = "newest",
        date_from_str: str | None = None,
        date_to_str: str | None = None,
        page: int = 1,
        limit: int = 20,
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

        # Auto-publish any due scheduled videos whose release date/time has passed
        self.repo.publish_due_scheduled_videos()

        videos, total = self.repo.get_all_videos_by_user(
            user_id=user_id,
            status=status_filter,
            category=category,
            search=search,
            sort=sort,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )

        # Sync live status/duration/published_at/available_resolutions for videos in PENDING/ENCODING/UPLOAD_FINISHED or missing metadata
        updated_videos = []
        pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
        for v in videos:
            if v.status in ("PENDING", "ENCODING", "PROCESSING", "UPLOAD_FINISHED") or (
                v.is_playable
                and (
                    not v.duration or not v.published_at or not v.available_resolutions
                )
            ):
                try:
                    status_data = get_bunny_video_status(v.bunny_video_id)
                    if status_data:
                        code = status_data.get("status")
                        prog = status_data.get("encodeProgress")
                        length = status_data.get("length")
                        duration_str = format_duration(length)

                        available_resolutions = None
                        if "availableResolutions" in status_data:
                            raw_res = status_data.get("availableResolutions")
                            if isinstance(raw_res, str):
                                available_resolutions = [
                                    r.strip() for r in raw_res.split(",") if r.strip()
                                ]
                            elif isinstance(raw_res, list):
                                available_resolutions = [
                                    str(r).strip() for r in raw_res if str(r).strip()
                                ]

                        captions_list = status_data.get("captions") or []
                        captions_data = []
                        if captions_list:
                            for idx, track in enumerate(captions_list):
                                if isinstance(track, dict) and track.get("srclang"):
                                    srclang = str(track.get("srclang")).strip()
                                    label = str(
                                        track.get("label") or srclang.upper()
                                    ).strip()
                                    captions_data.append(
                                        {
                                            "srclang": srclang,
                                            "label": label,
                                            "is_default": (idx == 0),
                                            "url": f"{pull_zone}/{v.bunny_video_id}/captions/{srclang}.vtt",
                                        }
                                    )

                        state = (
                            resolve_bunny_status(code, live_progress=prog)
                            if code is not None
                            else None
                        )
                        if state:
                            v = (
                                self.repo.update_video_status(
                                    bunny_video_id=v.bunny_video_id,
                                    status=state.db_status,
                                    encode_progress=state.progress,
                                    is_playable=state.is_playable,
                                    captions_data=captions_data
                                    if captions_data
                                    else None,
                                    available_resolutions=available_resolutions,
                                    duration=duration_str,
                                )
                                or v
                            )
                except Exception as e:  # noqa: BLE001
                    logger.warning(
                        "Failed auto-sync duration for video %s: %s",
                        v.bunny_video_id,
                        e,
                    )
            updated_videos.append(v)

        items = [self._to_video_list_item_response(v) for v in updated_videos]
        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def get_video_details(self, user_id: int, video_id: int) -> VideoResponse:
        """
        Retrieves detailed metadata for a single video. Syncs live encoding status from Bunny Stream if ENCODING.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )

        if video.status in ("PENDING", "ENCODING", "PROCESSING", "UPLOAD_FINISHED") or (
            video.is_playable
            and (
                not video.duration
                or not video.published_at
                or not video.available_resolutions
            )
        ):
            try:
                status_data = get_bunny_video_status(video.bunny_video_id)
                if status_data and "status" in status_data:
                    code = status_data.get("status")
                    prog = status_data.get("encodeProgress")
                    length = status_data.get("length")
                    duration_str = format_duration(length)

                    available_resolutions = None
                    if "availableResolutions" in status_data:
                        raw_res = status_data.get("availableResolutions")
                        if isinstance(raw_res, str):
                            available_resolutions = [
                                r.strip() for r in raw_res.split(",") if r.strip()
                            ]
                        elif isinstance(raw_res, list):
                            available_resolutions = [
                                str(r).strip() for r in raw_res if str(r).strip()
                            ]

                    captions_list = status_data.get("captions") or []
                    captions_data = []
                    if captions_list:
                        pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
                        for idx, track in enumerate(captions_list):
                            if isinstance(track, dict) and track.get("srclang"):
                                srclang = str(track.get("srclang")).strip()
                                label = str(
                                    track.get("label") or srclang.upper()
                                ).strip()
                                captions_data.append(
                                    {
                                        "srclang": srclang,
                                        "label": label,
                                        "is_default": (idx == 0),
                                        "url": f"{pull_zone}/{video.bunny_video_id}/captions/{srclang}.vtt",
                                    }
                                )

                    state = resolve_bunny_status(code, live_progress=prog)
                    if state:
                        video = (
                            self.repo.update_video_status(
                                bunny_video_id=video.bunny_video_id,
                                status=state.db_status,
                                encode_progress=state.progress,
                                is_playable=state.is_playable,
                                captions_data=captions_data if captions_data else None,
                                available_resolutions=available_resolutions,
                                duration=duration_str,
                            )
                            or video
                        )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Live status sync skipped for video %s: %s",
                    video.bunny_video_id,
                    e,
                )

        return self._to_video_response(video)

    def update_video_metadata(
        self, user_id: int, video_id: int, payload: VideoUpdateRequest
    ) -> VideoUpdateResponse:
        """
        Validates ownership and applies partial textual metadata updates (title, description, category, tags) in DB.
        """
        update_data = payload.model_dump(exclude_unset=True)
        if "tags" in update_data:
            update_data["tags"] = normalize_tags(update_data["tags"])

        video = self.repo.update_video_metadata(video_id, user_id, update_data)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )
        return self._to_video_update_response(video)

    def upload_thumbnail_image(
        self, user_id: int, video_id: int, slot: int, file: UploadFile
    ) -> ActionSuccessResponse:
        """
        Uploads thumbnail binary image for slot 0 (Bunny Stream API) or slot 1/2 (Bunny Storage API) via server proxy.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )

        if slot not in (0, 1, 2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thumbnail slot must be 0, 1, or 2",
            )

        settings = get_settings()
        new_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"{video.bunny_video_id}/thumb_{slot + 1}",
            max_size_mb=settings.MAX_THUMBNAIL_SIZE_MB,
        )
        self.repo.update_thumbnail_url(video_id, user_id, slot, new_url)

        return ActionSuccessResponse(status="success")

    def select_main_thumbnail(
        self, user_id: int, video_id: int, payload: SelectMainThumbnailRequest
    ) -> ActionSuccessResponse:
        """
        Executes thumbnail swapping logic between main cover and alt thumbnails in DB.
        """
        video = self.repo.swap_main_thumbnail(
            video_id, user_id, payload.selected_main_thumbnail
        )
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )
        return ActionSuccessResponse(status="success")

    def delete_alternative_thumbnail(
        self, user_id: int, video_id: int, payload: DeleteThumbnailRequest
    ) -> ActionSuccessResponse:
        """
        Issues HTTP DELETE to Bunny Storage API to remove physical cloud image and updates DB list.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )

        target_url = payload.thumbnail_url
        file_path = f"{video.bunny_video_id}/{target_url.split('/')[-1]}"
        try:
            delete_bunny_storage_file(file_path)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to delete Bunny Storage thumbnail file %s: %s",
                file_path,
                e,
            )

        self.repo.delete_alt_thumbnail_url(video_id, user_id, target_url)
        return ActionSuccessResponse(status="success")

    def _purge_cloud_video_assets(self, video) -> None:
        """
        Helper method to purge Bunny Stream container and all Bunny Storage thumbnails for a video asset.
        """
        try:
            delete_bunny_video(video.bunny_video_id)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to delete Bunny Stream container for video %s: %s",
                video.bunny_video_id,
                e,
            )

        all_thumb_urls = (
            [video.main_thumbnail_url] if video.main_thumbnail_url else []
        ) + list(video.alt_thumbnail_urls or [])
        for url in all_thumb_urls:
            if url and "b-cdn.net" in url:
                try:
                    file_path = f"{video.bunny_video_id}/{url.split('/')[-1]}"
                    delete_bunny_storage_file(file_path)
                except Exception as e:  # noqa: BLE001
                    logger.warning(
                        "Failed to delete Bunny Storage thumbnail %s: %s",
                        url,
                        e,
                    )

    def delete_video_asset(self, user_id: int, video_id: int) -> ActionSuccessResponse:
        """
        Issues HTTP DELETE to Bunny Stream API to remove cloud video container, deletes all storage thumbnails, and drops video record from DB.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )

        self._purge_cloud_video_assets(video)
        self.repo.delete_video(video_id, user_id)
        return ActionSuccessResponse(status="success")

    def bulk_delete_videos(
        self, user_id: int, payload: BulkDeleteVideosRequest
    ) -> ActionSuccessResponse:
        """
        Bulk deletes multiple video assets by ID array owned by creator along with cloud video containers and storage thumbnails.
        """
        deleted_videos = self.repo.bulk_delete_videos(payload.video_ids, user_id)
        for video in deleted_videos:
            self._purge_cloud_video_assets(video)

        return ActionSuccessResponse(status="success")

    def publish_video_immediately(
        self, user_id: int, video_id: int
    ) -> VideoPublishResponse:
        """
        Publishes a video asset immediately, updating state to 'published' and recording published_at timestamp.
        """
        video = self.repo.publish_video(video_id, user_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )

        return VideoPublishResponse(
            id=video.id, status=video.status, published_at=video.published_at
        )

    def schedule_video_publication(
        self, user_id: int, video_id: int, payload: VideoScheduleRequest
    ) -> VideoScheduleResponse:
        """
        Schedules a video asset for future publication, parsing local date/time as-is.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset {video_id} not found",
            )

        try:
            scheduled_dt_str = f"{payload.date} {payload.time}"
            scheduled_dt = datetime.strptime(
                scheduled_dt_str, "%Y-%m-%d %H:%M"
            ).replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date or time specification: {e!s}",
            ) from e

        updated_video = self.repo.schedule_video(video_id, user_id, scheduled_dt)
        return VideoScheduleResponse(
            id=updated_video.id,
            status=updated_video.status,
            scheduled_at=updated_video.scheduled_at,
        )
