import logging
import math
import time
import base64
import requests
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
    upload_bunny_storage_file,
    delete_bunny_storage_file,
    add_bunny_video_caption
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


def format_duration(seconds: Optional[int]) -> Optional[str]:
    """Formats integer seconds into MM:SS or HH:MM:SS string."""
    if not seconds or seconds <= 0:
        return None
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def normalize_tags(tags: Optional[List[str]]) -> List[str]:
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

def normalize_caption_track(track: dict):
    """
    Normalizes AI auto-generated caption language codes (e.g. 'en-auto' -> 'en')
    and returns (raw_srclang, clean_srclang, clean_label).
    """
    if not isinstance(track, dict):
        return None, None, None
    raw_srclang = str(track.get("srclang", "")).strip()
    if not raw_srclang:
        return None, None, None
    clean_srclang = raw_srclang.lower().replace("-auto", "").replace("_auto", "").strip()
    raw_label = str(track.get("label", "")).strip()
    clean_label = raw_label.replace("-auto", "").replace("(auto)", "").replace("(en-auto)", "").strip()
    if not clean_label:
        clean_label = clean_srclang.upper()
    return raw_srclang, clean_srclang, clean_label

def extract_available_captions(captions_data: Optional[list]) -> List[str]:
    """
    Extracts a list of clean, unique caption labels from raw DB captions_data JSON.
    Example: [{"label": "EN"}, {"label": "HI"}] -> ["EN", "HI"]
    """
    if not captions_data or not isinstance(captions_data, list):
        return []
    labels = []
    for c in captions_data:
        if isinstance(c, dict):
            lbl = c.get("label") or c.get("srclang")
            if lbl and lbl not in labels:
                labels.append(lbl)
    return labels

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
            available_captions=extract_available_captions(video.captions_data),
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
            available_captions=extract_available_captions(video.captions_data),
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
            bunny_api_key=api_key,
            expiration_time=expiration_timestamp,
            video_id=bunny_video_id
        )

        main_thumbnail_url = None
        alt_thumbnail_urls = []

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
        logger.info(f"📥 Received Bunny Stream Webhook Event: Status={status_code}, VideoGuid={payload.VideoGuid}")
        state = resolve_bunny_status(status_code)

        if not state:
            logger.warning(f"Unrecognized Bunny webhook status code {status_code} for video {payload.VideoGuid}")
            return ActionSuccessResponse(status="success")

        # Sync video duration and captions metadata from Bunny Stream API
        duration_str = None
        captions_list = []
        try:
            status_data = get_bunny_video_status(payload.VideoGuid)
            if status_data:
                if "length" in status_data:
                    duration_str = format_duration(status_data.get("length"))
                captions_list = status_data.get("captions") or []
                logger.info(f"Fetched Bunny Stream status for {payload.VideoGuid}: length={duration_str}, captions={captions_list}")
        except Exception as e:
            logger.warning(f"Failed to fetch Bunny Stream status for {payload.VideoGuid}: {str(e)}")

        # Build clean captions_data array
        captions_data = []
        if captions_list:
            pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
            for idx, track in enumerate(captions_list):
                raw_srclang, clean_srclang, clean_label = normalize_caption_track(track)
                if not clean_srclang:
                    continue
                captions_data.append({
                    "srclang": clean_srclang,
                    "label": clean_label,
                    "is_default": (idx == 0),
                    "url": f"{pull_zone}/{payload.VideoGuid}/captions/{clean_srclang}.vtt"
                })

        if status_code in (3, 4, 9, 10) and captions_list:
            logger.info(f"Triggering HLS Caption Re-Registration for video {payload.VideoGuid} with captions: {captions_list}")
            settings = get_settings()
            stream_headers = {
                "AccessKey": settings.BUNNY_STREAM_API_KEY,
                "accept": "application/json"
            }
            for track in captions_list:
                raw_srclang, clean_srclang, clean_label = normalize_caption_track(track)
                if not raw_srclang or not clean_srclang:
                    continue
                # If Bunny returned an auto-generated track (e.g. en-auto), fetch and re-upload as clean track (e.g. en)
                try:
                    stream_vtt_url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{payload.VideoGuid}/captions/{raw_srclang}"
                    logger.info(f"Fetching VTT file from Bunny Stream REST API: {stream_vtt_url}")
                    vtt_resp = requests.get(stream_vtt_url, headers=stream_headers, timeout=10)
                    logger.info(f"VTT GET Response Status: {vtt_resp.status_code}, Length: {len(vtt_resp.text) if vtt_resp.text else 0}")
                    if vtt_resp.status_code == 200 and vtt_resp.text:
                        vtt_b64 = base64.b64encode(vtt_resp.text.encode("utf-8")).decode("utf-8")
                        res = add_bunny_video_caption(payload.VideoGuid, srclang=clean_srclang, label=clean_label, caption_vtt_base64=vtt_b64)
                        logger.info(f"✅ Successfully auto-registered '{clean_label}' ({clean_srclang}) caption into playlist.m3u8 for video {payload.VideoGuid} | Result: {res}")
                except Exception as e:
                    logger.warning(f"❌ Failed to auto-register '{clean_srclang}' caption for video {payload.VideoGuid}: {str(e)}")

        self.repo.update_video_status(
            bunny_video_id=payload.VideoGuid,
            status=state.db_status,
            encode_progress=state.progress,
            is_playable=state.is_playable,
            captions_data=captions_data,
            duration=duration_str
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
            limit=limit
        )

        # Sync live status/duration/published_at for videos in PENDING/ENCODING/UPLOAD_FINISHED or missing duration
        updated_videos = []
        pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
        for v in videos:
            if v.status in ("PENDING", "ENCODING", "PROCESSING", "UPLOAD_FINISHED") or (v.is_playable and (not v.duration or not v.published_at or not v.captions_data)):
                try:
                    status_data = get_bunny_video_status(v.bunny_video_id)
                    if status_data:
                        code = status_data.get("status")
                        prog = status_data.get("encodeProgress")
                        length = status_data.get("length")
                        duration_str = format_duration(length)
                        captions_list = status_data.get("captions") or []
                        captions_data = []
                        if captions_list:
                            settings = get_settings()
                            stream_headers = {
                                "AccessKey": settings.BUNNY_STREAM_API_KEY,
                                "accept": "application/json"
                            }
                            for idx, track in enumerate(captions_list):
                                raw_srclang, clean_srclang, clean_label = normalize_caption_track(track)
                                if not clean_srclang:
                                    continue
                                captions_data.append({
                                    "srclang": clean_srclang,
                                    "label": clean_label,
                                    "is_default": (idx == 0),
                                    "url": f"{pull_zone}/{v.bunny_video_id}/captions/{clean_srclang}.vtt"
                                })
                                # Re-register auto-generated captions to bake into playlist.m3u8
                                if raw_srclang and "-auto" in raw_srclang:
                                    try:
                                        stream_vtt_url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{v.bunny_video_id}/captions/{raw_srclang}"
                                        vtt_resp = requests.get(stream_vtt_url, headers=stream_headers, timeout=10)
                                        if vtt_resp.status_code == 200 and vtt_resp.text:
                                            vtt_b64 = base64.b64encode(vtt_resp.text.encode("utf-8")).decode("utf-8")
                                            res = add_bunny_video_caption(v.bunny_video_id, srclang=clean_srclang, label=clean_label, caption_vtt_base64=vtt_b64)
                                            logger.info(f"✅ Live-Sync Auto-Registered '{clean_label}' ({clean_srclang}) caption into playlist.m3u8 for video {v.bunny_video_id}")
                                    except Exception as e:
                                        logger.warning(f"Failed live-sync auto-register for video {v.bunny_video_id}: {str(e)}")

                        state = resolve_bunny_status(code, live_progress=prog) if code is not None else None
                        if state:
                            v = self.repo.update_video_status(
                                bunny_video_id=v.bunny_video_id,
                                status=state.db_status,
                                encode_progress=state.progress,
                                is_playable=state.is_playable,
                                captions_data=captions_data if captions_data else None,
                                duration=duration_str
                            ) or v
                except Exception as e:
                    logger.warning(f"Failed auto-sync duration for video {v.bunny_video_id}: {str(e)}")
            updated_videos.append(v)

        items = [self._to_video_list_item_response(v) for v in updated_videos]
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

        if video.status in ("PENDING", "ENCODING", "PROCESSING", "UPLOAD_FINISHED") or (video.is_playable and (not video.duration or not video.published_at or not video.captions_data)):
            try:
                status_data = get_bunny_video_status(video.bunny_video_id)
                if status_data and "status" in status_data:
                    code = status_data.get("status")
                    prog = status_data.get("encodeProgress")
                    length = status_data.get("length")
                    duration_str = format_duration(length)
                    captions_list = status_data.get("captions") or []
                    captions_data = []
                    if captions_list:
                        pull_zone = get_settings().BUNNY_PULL_ZONE_URL.rstrip("/")
                        settings = get_settings()
                        stream_headers = {
                            "AccessKey": settings.BUNNY_STREAM_API_KEY,
                            "accept": "application/json"
                        }
                        for idx, track in enumerate(captions_list):
                            raw_srclang, clean_srclang, clean_label = normalize_caption_track(track)
                            if not clean_srclang:
                                continue
                            captions_data.append({
                                "srclang": clean_srclang,
                                "label": clean_label,
                                "is_default": (idx == 0),
                                "url": f"{pull_zone}/{video.bunny_video_id}/captions/{clean_srclang}.vtt"
                            })
                            # Re-register auto-generated captions to bake into playlist.m3u8
                            if raw_srclang and "-auto" in raw_srclang:
                                try:
                                    stream_vtt_url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{video.bunny_video_id}/captions/{raw_srclang}"
                                    vtt_resp = requests.get(stream_vtt_url, headers=stream_headers, timeout=10)
                                    if vtt_resp.status_code == 200 and vtt_resp.text:
                                        vtt_b64 = base64.b64encode(vtt_resp.text.encode("utf-8")).decode("utf-8")
                                        res = add_bunny_video_caption(video.bunny_video_id, srclang=clean_srclang, label=clean_label, caption_vtt_base64=vtt_b64)
                                        logger.info(f"✅ Live-Sync Auto-Registered '{clean_label}' ({clean_srclang}) caption into playlist.m3u8 for video {video.bunny_video_id}")
                                except Exception as e:
                                    logger.warning(f"Failed live-sync auto-register for video {video.bunny_video_id}: {str(e)}")

                    state = resolve_bunny_status(code, live_progress=prog)
                    if state:
                        video = self.repo.update_video_status(
                            bunny_video_id=video.bunny_video_id,
                            status=state.db_status,
                            encode_progress=state.progress,
                            is_playable=state.is_playable,
                            captions_data=captions_data if captions_data else None,
                            duration=duration_str
                        ) or video
            except Exception as e:
                logger.warning(f"Live status sync skipped for video {video.bunny_video_id}: {str(e)}")

        return self._to_video_response(video)

    def update_video_metadata(self, user_id: int, video_id: int, payload: VideoUpdateRequest) -> VideoUpdateResponse:
        """
        Validates ownership and applies partial textual metadata updates (title, description, category, tags) in DB.
        """
        update_data = payload.model_dump(exclude_unset=True)
        if "tags" in update_data:
            update_data["tags"] = normalize_tags(update_data["tags"])

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
        filename = f"thumb_{slot + 1}.{ext}"

        file_path = f"{video.bunny_video_id}/{filename}"
        upload_bunny_storage_file(file_path, file_bytes, content_type)

        settings = get_settings()
        storage_pull_zone = settings.BUNNY_STORAGE_PULL_ZONE_URL.rstrip("/")
        new_url = f"{storage_pull_zone}/{video.bunny_video_id}/{filename}"
        self.repo.update_thumbnail_url(video_id, user_id, slot, new_url)

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

    def _purge_cloud_video_assets(self, video) -> None:
        """
        Helper method to purge Bunny Stream container and all Bunny Storage thumbnails for a video asset.
        """
        try:
            delete_bunny_video(video.bunny_video_id)
        except Exception as e:
            logger.warning(f"Failed to delete Bunny Stream container for video {video.bunny_video_id}: {str(e)}")

        all_thumb_urls = ([video.main_thumbnail_url] if video.main_thumbnail_url else []) + list(video.alt_thumbnail_urls or [])
        for url in all_thumb_urls:
            if url and "b-cdn.net" in url:
                try:
                    file_path = f"{video.bunny_video_id}/{url.split('/')[-1]}"
                    delete_bunny_storage_file(file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete Bunny Storage thumbnail {url}: {str(e)}")

    def delete_video_asset(self, user_id: int, video_id: int) -> ActionSuccessResponse:
        """
        Issues HTTP DELETE to Bunny Stream API to remove cloud video container, deletes all storage thumbnails, and drops video record from DB.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        self._purge_cloud_video_assets(video)
        self.repo.delete_video(video_id, user_id)
        return ActionSuccessResponse(status="success")

    def bulk_delete_videos(self, user_id: int, payload: BulkDeleteVideosRequest) -> ActionSuccessResponse:
        """
        Bulk deletes multiple video assets by ID array owned by creator along with cloud video containers and storage thumbnails.
        """
        deleted_videos = self.repo.bulk_delete_videos(payload.video_ids, user_id)
        for video in deleted_videos:
            self._purge_cloud_video_assets(video)

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
        Schedules a video asset for future publication, parsing local date/time as-is.
        """
        video = self.repo.get_video_by_id(video_id, user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video asset {video_id} not found")

        try:
            scheduled_dt_str = f"{payload.date} {payload.time}"
            scheduled_dt = datetime.strptime(scheduled_dt_str, "%Y-%m-%d %H:%M")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date or time specification: {str(e)}"
            )

        updated_video = self.repo.schedule_video(video_id, user_id, scheduled_dt)
        return VideoScheduleResponse(
            id=updated_video.id,
            status=updated_video.status,
            scheduled_at=updated_video.scheduled_at
        )
