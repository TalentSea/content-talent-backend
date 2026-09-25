import logging

from fastapi import HTTPException, status

from app.config import get_settings
from app.repositories.mobile.user_subscription_repository import (
    UserSubscriptionRepository,
)
from app.repositories.mobile.video_repository import MobileVideoRepository
from app.schemas.mobile.video_schemas import (
    CreatorBrandingSummary,
    MobileShortItemResponse,
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
        self.sub_repo = UserSubscriptionRepository()

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
            video_type=v.resolved_video_type,
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
        tenant_id: int | None = None,
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
            tenant_id=tenant_id,
            category=category,
            search=search,
            sort=sort,
            page=page,
            limit=limit,
        )
        items = self._build_list_item_responses(videos, subscriber_id=subscriber_id)
        return self._build_paginated_response(items, total_count, page, limit)

    def list_shorts(
        self,
        tenant_id: int,
        sort: str = "newest",
        page: int = 1,
        limit: int = 10,
        subscriber_id: int | None = None,
    ) -> PaginatedResponse[MobileShortItemResponse]:
        """
        Retrieves a paginated list of published & ready short videos for the vertical swipe Reels feed.
        HLS streaming URLs are presigned with time-bound Bunny tokens.
        100% ad-free, no downloads, no categories.
        Attaches creator studio branding, captions, and personalized engagement status.
        """
        shorts, total_count = self.repo.list_published_shorts(
            tenant_id=tenant_id,
            sort=sort,
            page=page,
            limit=limit,
        )

        video_ids = [s.id for s in shorts]
        likes_map, comments_map, liked_set, saved_set = (
            self.repo.get_shorts_engagement_map(video_ids, subscriber_id=subscriber_id)
        )

        settings = get_settings()
        pull_zone_url = settings.BUNNY_PULL_ZONE_URL
        token_key = settings.BUNNY_STREAM_TOKEN_KEY
        base_cdn = pull_zone_url.rstrip("/") if pull_zone_url else ""

        items = []
        for s in shorts:
            # Presigned HLS Stream URL
            hls_url = ""
            if s.bunny_video_id and pull_zone_url and token_key:
                hls_url = generate_signed_playback_url(
                    bunny_pull_zone_url=pull_zone_url,
                    bunny_video_id=s.bunny_video_id,
                    token_security_key=token_key,
                )

            # Captions
            captions = []
            if s.captions_data:
                for cap in s.captions_data:
                    if isinstance(cap, dict) and cap.get("srclang"):
                        srclang = str(cap.get("srclang")).strip()
                        lang_name = str(cap.get("label") or srclang.capitalize()).strip()
                        vtt_url = (
                            cap.get("url")
                            or f"{base_cdn}/{s.bunny_video_id}/captions/{srclang}.vtt"
                        )
                        captions.append(
                            MobileVideoCaptionResponse(
                                language=lang_name,
                                srclang=srclang,
                                url=vtt_url,
                            )
                        )

            # Creator Studio Branding
            creator_name = s.tenant.name if s.tenant else "Creator Studio"
            creator_logo = s.tenant.logo_url if s.tenant else None
            creator_summary = CreatorBrandingSummary(
                name=creator_name,
                logo_url=creator_logo,
            )

            dur_sec = parse_duration_seconds(s.duration)

            items.append(
                MobileShortItemResponse(
                    id=s.id,
                    title=s.title,
                    description=s.description,
                    thumbnail_url=s.main_thumbnail_url,
                    duration=dur_sec,
                    views_count=s.views or 0,
                    likes_count=likes_map.get(s.id, 0),
                    comments_count=comments_map.get(s.id, 0),
                    is_liked=s.id in liked_set,
                    is_saved=s.id in saved_set,
                    hls_stream_url=hls_url,
                    captions=captions,
                    creator=creator_summary,
                    published_at=s.published_at,
                )
            )

        return PaginatedResponse.create(
            items=items,
            total=total_count,
            page=page,
            limit=limit,
        )

    def get_video_details(
        self,
        video_id: int,
        subscriber_id: int | None = None,
        tenant_id: int | None = None,
    ) -> MobileVideoDetailResponse:
        """
        Fetches detailed video metadata and generates presigned HLS streaming URL + MP4 download URLs.
        Dynamically calculates total likes count, is_liked, is_saved, and watch progress.
        """
        video = self.repo.get_public_video_by_id(video_id, tenant_id=tenant_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )

        settings = get_settings()
        pull_zone_url = settings.BUNNY_PULL_ZONE_URL
        token_key = settings.BUNNY_STREAM_TOKEN_KEY

        # 1. Evaluate Active Subscription Entitlement for this Creator Studio
        active_sub = None
        if subscriber_id:
            active_sub = self.sub_repo.get_active_subscription(
                user_id=subscriber_id, tenant_id=video.tenant_id
            )

        hls_stream_url: str | None = None
        download_urls: list[MobileVideoDownloadUrlResponse] | None = None
        captions: list[MobileVideoCaptionResponse] | None = None
        ad_tag_url: str | None = None
        is_short = video.is_short

        if active_sub:
            # 2. Grant Presigned HLS Stream URL to active subscribers
            if video.bunny_video_id and pull_zone_url:
                hls_stream_url = generate_signed_playback_url(
                    bunny_pull_zone_url=pull_zone_url,
                    bunny_video_id=video.bunny_video_id,
                    token_security_key=token_key,
                )

                # Dynamically Generate Presigned MP4 Download URLs (strictly standard videos only; shorts are streaming-only)
                if not is_short:
                    download_urls = []
                    avail_res = (
                        video.available_resolutions
                        if isinstance(video.available_resolutions, list)
                        else []
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

                # Generate Closed Captions VTT tracks
                captions = []
                if video.captions_data:
                    base_cdn = pull_zone_url.rstrip("/")
                    for cap in video.captions_data:
                        if isinstance(cap, dict) and cap.get("srclang"):
                            srclang = str(cap.get("srclang")).strip()
                            lang_name = str(cap.get("label") or srclang.capitalize()).strip()
                            vtt_url = (
                                cap.get("url")
                                or f"{base_cdn}/{video.bunny_video_id}/captions/{srclang}.vtt"
                            )
                            captions.append(
                                MobileVideoCaptionResponse(
                                    language=lang_name,
                                    srclang=srclang,
                                    url=vtt_url,
                                    )
                            )

            # 3. Evaluate Ad Tag URL based on subscriber's plan type (shorts are strictly 100% ad-free)
            plan_type = getattr(active_sub.plan, "plan_type", "with_ads")
            if plan_type == "with_ads" and not is_short:
                vast_tag = (
                    settings.GOOGLE_IMA_VAST_TAG_URL.strip()
                    if settings.GOOGLE_IMA_VAST_TAG_URL
                    else None
                )
                if vast_tag:
                    delimiter = "&" if ("?" in vast_tag) else "?"
                    cust_params = f"cust_params=tenant_id%3D{video.tenant_id}%26video_id%3D{video.id}"
                    ad_tag_url = f"{vast_tag}{delimiter}{cust_params}"
            # If plan_type == "no_ads" or is_short == True, ad_tag_url remains None (100% ad-free)

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
            category=None if is_short else video.category,
            video_type=video.resolved_video_type,
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
            ad_tag_url=ad_tag_url,
            download_urls=download_urls,
            captions=captions,
            published_at=video.published_at,
        )


    def record_video_view(
        self, video_id: int, subscriber_id: int, tenant_id: int | None = None
    ) -> MobileViewCountResponse:
        """
        Increments views counter for a published video asset after validating
        backend 30% threshold and anti-spam debouncing.
        """
        try:
            new_views = self.repo.increment_view_count(
                video_id=video_id,
                subscriber_id=subscriber_id,
                tenant_id=tenant_id,
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
        tenant_id: int | None = None,
    ) -> MobileVideoLikeResponse:
        """
        Toggles subscriber like state for a published video asset.
        """
        result = self.repo.toggle_video_like(
            video_id, subscriber_id, tenant_id=tenant_id
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
        tenant_id: int | None = None,
    ) -> MobileVideoSaveResponse:
        """
        Toggles subscriber save/bookmark state for a published video asset.
        """
        is_saved = self.repo.toggle_video_save(
            video_id, subscriber_id, tenant_id=tenant_id
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
        tenant_id: int | None = None,
    ):
        """
        Updates playback watch position from subscriber mobile player heartbeat.
        """
        success = self.repo.update_watch_progress(
            video_id=video_id,
            subscriber_id=subscriber_id,
            progress_seconds=progress_seconds,
            tenant_id=tenant_id,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )

    def list_subscriber_liked_videos(
        self,
        subscriber_id: int,
        tenant_id: int | None = None,
        video_type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves a paginated list of videos liked by the calling subscriber ("My Liked Videos").
        Optionally filtered by video_type ('shorts' or 'standard').
        """
        videos, total_count = self.repo.list_subscriber_liked_videos(
            subscriber_id=subscriber_id,
            tenant_id=tenant_id,
            video_type=video_type,
            page=page,
            limit=limit,
        )

        items = self._build_list_item_responses(videos, subscriber_id=subscriber_id)
        return self._build_paginated_response(items, total_count, page, limit)

    def list_subscriber_saved_videos(
        self,
        subscriber_id: int,
        tenant_id: int | None = None,
        video_type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves a paginated list of videos saved by the calling subscriber ("My Watchlist").
        Optionally filtered by video_type ('shorts' or 'standard').
        """
        videos, total_count = self.repo.list_subscriber_saved_videos(
            subscriber_id=subscriber_id,
            tenant_id=tenant_id,
            video_type=video_type,
            page=page,
            limit=limit,
        )

        items = self._build_list_item_responses(videos, subscriber_id=subscriber_id)
        return self._build_paginated_response(items, total_count, page, limit)

    def list_continue_watching_videos(
        self,
        subscriber_id: int,
        tenant_id: int | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves paginated unfinished videos for subscriber 'Continue Watching' carousel.
        """
        tuples_list, total_count = self.repo.list_continue_watching_videos(
            subscriber_id=subscriber_id,
            tenant_id=tenant_id,
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
        tenant_id: int | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[MobileVideoListItemResponse]:
        """
        Retrieves paginated watch history for calling subscriber.
        """
        tuples_list, total_count = self.repo.list_watch_history(
            subscriber_id=subscriber_id,
            tenant_id=tenant_id,
            page=page,
            limit=limit,
        )

        items = [
            self._to_list_item_response(v, pos=pos, pct=pct)
            for v, pos, pct in tuples_list
        ]
        return self._build_paginated_response(items, total_count, page, limit)

    def clear_watch_history(self, subscriber_id: int, tenant_id: int | None = None):
        """
        Deletes all watch history for calling subscriber.
        """
        self.repo.clear_watch_history(subscriber_id, tenant_id=tenant_id)

    def remove_video_from_watch_history(
        self, video_id: int, subscriber_id: int, tenant_id: int | None = None
    ):
        """
        Deletes single video watch history record for calling subscriber.
        """
        success = self.repo.remove_video_from_watch_history(
            video_id=video_id, subscriber_id=subscriber_id, tenant_id=tenant_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Published video with ID {video_id} not found",
            )
