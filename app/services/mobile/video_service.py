import logging

from fastapi import HTTPException, status

from app.config import get_settings
from app.repositories.mobile.video_repository import MobileVideoRepository
from app.schemas.mobile.video_schemas import (
    MobileVideoCaptionResponse,
    MobileVideoDetailResponse,
    MobileVideoDownloadUrlResponse,
    MobileVideoLikeResponse,
    MobileVideoListItemResponse,
    MobileVideoSaveResponse,
    MobileViewCountResponse,
)
from app.schemas.shared.common_schemas import PaginatedResponse
from app.utils.bunny_signature import (
    generate_signed_mp4_url,
    generate_signed_playback_url,
)
from app.utils.formatters import parse_duration_seconds

logger = logging.getLogger(__name__)


class MobileVideoService:
    """
    Business logic service for Mobile Subscriber Video catalog, HLS presigned streaming, MP4 downloads, and Watch History.
    """

    def __init__(self):
        self.repo = MobileVideoRepository()

    def _to_list_item_response(
        self, v, pos: int | None = None, pct: float | None = None
    ) -> MobileVideoListItemResponse:
        return MobileVideoListItemResponse(
            id=v.id,
            title=v.title,
            thumbnail_url=v.main_thumbnail_url,
            duration=parse_duration_seconds(v.duration),
            views_count=v.views or 0,
            category=v.category,
            last_position_seconds=pos,
            progress_percentage=pct,
            published_at=v.published_at,
        )

    def _build_list_item_responses(
        self, videos: list, subscriber_id: int | None = None
    ) -> list[MobileVideoListItemResponse]:
        progress_map = {}
        if subscriber_id and videos:
            progress_map = self.repo.get_subscriber_watch_progress_map(
                subscriber_id, [v.id for v in videos]
            )

        items = []
        for v in videos:
            pos, pct = progress_map.get(v.id, (None, None))
            items.append(self._to_list_item_response(v, pos=pos, pct=pct))
        return items

    def _build_paginated_response(
        self, items: list, total_count: int, page: int, limit: int
    ) -> PaginatedResponse:
        return PaginatedResponse.create(
            items=items, total=total_count, page=page, limit=limit
        )

    def list_public_videos(
        self,
        creator_id: int | None = None,
        category: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
        subscriber_id: int | None = None,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves a paginated list of published & ready video items for public mobile feed.
        Attaches personalized watch progress if subscriber_id is provided.
        """
        videos, total_count = self.repo.list_public_videos(
            creator_id=creator_id,
            category=category,
            search=search,
            sort=sort,
            page=page,
            limit=limit,
        )
        items = self._build_list_item_responses(videos, subscriber_id=subscriber_id)
        return self._build_paginated_response(items, total_count, page, limit)

    def get_video_details(
        self,
        video_id: int,
        subscriber_id: int | None = None,
        creator_id: int | None = None,
    ) -> MobileVideoDetailResponse:
        """
        Fetches detailed video metadata and generates presigned HLS streaming URL + MP4 download URLs.
        Dynamically calculates total likes count, is_liked, is_saved, and watch progress.
        """
        video = self.repo.get_public_video_by_id(video_id, creator_id=creator_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )

        settings = get_settings()
        pull_zone_url = settings.BUNNY_PULL_ZONE_URL
        token_key = settings.BUNNY_STREAM_TOKEN_KEY

        # 1. Generate Presigned HLS Playback URL (playlist.m3u8?token=...&expires=...)
        hls_stream_url = None
        if video.bunny_video_id and pull_zone_url:
            hls_stream_url = generate_signed_playback_url(
                bunny_pull_zone_url=pull_zone_url,
                bunny_video_id=video.bunny_video_id,
                token_security_key=token_key,
            )

        # 2. Dynamically Generate Presigned MP4 Download URLs for available resolutions
        download_urls: list[MobileVideoDownloadUrlResponse] = []
        if video.bunny_video_id and pull_zone_url:
            avail_res = (
                video.available_resolutions
                if isinstance(video.available_resolutions, list)
                and video.available_resolutions
                else ["1080p", "720p", "480p", "360p"]
            )
            for res in avail_res:
                mp4_url = generate_signed_mp4_url(
                    bunny_pull_zone_url=pull_zone_url,
                    bunny_video_id=video.bunny_video_id,
                    resolution=res,
                    token_security_key=token_key,
                )
                download_urls.append(
                    MobileVideoDownloadUrlResponse(resolution=res, url=mp4_url)
                )

        # 3. Generate Closed Captions VTT tracks
        captions: list[MobileVideoCaptionResponse] = []
        if video.bunny_video_id and pull_zone_url:
            base_cdn = pull_zone_url.rstrip("/")
            captions.append(
                MobileVideoCaptionResponse(
                    language="English",
                    srclang="en",
                    url=f"{base_cdn}/{video.bunny_video_id}/captions/en.vtt",
                )
            )

        tags_list = (
            list(video.tags or [])
            if isinstance(video.tags, (list, tuple))
            else [t.strip() for t in (video.tags or "").split(",") if t.strip()]
        )
        duration_secs = parse_duration_seconds(video.duration)

        # 4. Calculate engagement state & watch progress
        likes_count = self.repo.get_video_likes_count(video.id)
        is_liked = False
        is_saved = False
        last_pos = 0
        progress_pct = 0.0

        if subscriber_id:
            is_liked = self.repo.is_video_liked_by_subscriber(video.id, subscriber_id)
            is_saved = self.repo.is_video_saved_by_subscriber(video.id, subscriber_id)
            last_pos, progress_pct = self.repo.get_subscriber_video_watch_progress(
                video.id, subscriber_id
            )

        return MobileVideoDetailResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            category=video.category,
            tags=tags_list,
            duration=duration_secs,
            views_count=video.views or 0,
            likes_count=likes_count,
            is_liked=is_liked,
            is_saved=is_saved,
            last_position_seconds=last_pos,
            progress_percentage=progress_pct,
            thumbnail_url=video.main_thumbnail_url,
            hls_stream_url=hls_stream_url,
            download_urls=download_urls,
            captions=captions,
            published_at=video.published_at,
        )

    def record_video_view(
        self, video_id: int, subscriber_id: int, creator_id: int | None = None
    ) -> MobileViewCountResponse:
        """
        Increments views counter for a published video asset after validating
        backend 30% threshold and anti-spam debouncing.
        """
        try:
            new_views = self.repo.increment_view_count(
                video_id=video_id,
                subscriber_id=subscriber_id,
                creator_id=creator_id,
            )
        except ValueError as err:
            if str(err) == "WATCH_THRESHOLD_NOT_MET":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="WATCH_THRESHOLD_NOT_MET",
                )
            raise

        if new_views is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )
        return MobileViewCountResponse(status="success", views_count=new_views)

    def toggle_video_like(
        self,
        video_id: int,
        subscriber_id: int,
        creator_id: int | None = None,
    ) -> MobileVideoLikeResponse:
        """
        Toggles subscriber like state for a published video asset.
        """
        result = self.repo.toggle_video_like(
            video_id, subscriber_id, creator_id=creator_id
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )

        is_liked, total_likes = result
        return MobileVideoLikeResponse(is_liked=is_liked, likes_count=total_likes)

    def toggle_video_save(
        self,
        video_id: int,
        subscriber_id: int,
        creator_id: int | None = None,
    ) -> MobileVideoSaveResponse:
        """
        Toggles subscriber save/bookmark state for a published video asset.
        """
        is_saved = self.repo.toggle_video_save(
            video_id, subscriber_id, creator_id=creator_id
        )
        if is_saved is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )

        return MobileVideoSaveResponse(is_saved=is_saved)

    def update_watch_progress(
        self,
        video_id: int,
        subscriber_id: int,
        progress_seconds: int,
        creator_id: int | None = None,
    ):
        """
        Updates playback watch position from subscriber mobile player heartbeat.
        """
        success = self.repo.update_watch_progress(
            video_id=video_id,
            subscriber_id=subscriber_id,
            progress_seconds=progress_seconds,
            creator_id=creator_id,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )

    def list_subscriber_liked_videos(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves a paginated list of videos liked by the calling subscriber ("My Liked Videos").
        """
        videos, total_count = self.repo.list_subscriber_liked_videos(
            subscriber_id=subscriber_id,
            creator_id=creator_id,
            page=page,
            limit=limit,
        )

        items = self._build_list_item_responses(videos, subscriber_id=subscriber_id)
        return self._build_paginated_response(items, total_count, page, limit)

    def list_subscriber_saved_videos(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves a paginated list of videos saved by the calling subscriber ("My Watchlist").
        """
        videos, total_count = self.repo.list_subscriber_saved_videos(
            subscriber_id=subscriber_id,
            creator_id=creator_id,
            page=page,
            limit=limit,
        )

        items = self._build_list_item_responses(videos, subscriber_id=subscriber_id)
        return self._build_paginated_response(items, total_count, page, limit)

    def list_continue_watching_videos(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves paginated unfinished videos for subscriber 'Continue Watching' carousel.
        """
        tuples_list, total_count = self.repo.list_continue_watching_videos(
            subscriber_id=subscriber_id,
            creator_id=creator_id,
            page=page,
            limit=limit,
        )

        items = [
            self._to_list_item_response(v, pos=pos, pct=pct)
            for v, pos, pct in tuples_list
        ]
        return self._build_paginated_response(items, total_count, page, limit)

    def list_watch_history(
        self,
        subscriber_id: int,
        creator_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves paginated watch history for calling subscriber.
        """
        tuples_list, total_count = self.repo.list_watch_history(
            subscriber_id=subscriber_id,
            creator_id=creator_id,
            page=page,
            limit=limit,
        )

        items = [
            self._to_list_item_response(v, pos=pos, pct=pct)
            for v, pos, pct in tuples_list
        ]
        return self._build_paginated_response(items, total_count, page, limit)

    def clear_watch_history(self, subscriber_id: int, creator_id: int | None = None):
        """
        Deletes all watch history for calling subscriber.
        """
        self.repo.clear_watch_history(subscriber_id, creator_id=creator_id)

    def remove_video_from_watch_history(
        self, video_id: int, subscriber_id: int, creator_id: int | None = None
    ):
        """
        Deletes single video watch history record for calling subscriber.
        """
        success = self.repo.remove_video_from_watch_history(
            video_id=video_id, subscriber_id=subscriber_id, creator_id=creator_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )
