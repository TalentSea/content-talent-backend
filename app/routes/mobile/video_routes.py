from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentSubscriber
from app.schemas.mobile.video_schemas import (
    MobileVideoDetailResponse,
    MobileVideoLikeResponse,
    MobileVideoListItemResponse,
    MobileVideoSaveResponse,
    MobileViewCountResponse,
    MobileWatchProgressRequest,
)
from app.schemas.shared.common_schemas import PaginatedResponse
from app.services.mobile.video_service import MobileVideoService

router = APIRouter(prefix="/api/v1/mobile/videos", tags=["Mobile Videos"])
mobile_video_service = MobileVideoService()


@router.get(
    "",
    response_model=PaginatedResponse[MobileVideoListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Video Catalog Feed",
    description="Retrieves a paginated, filterable list of published, ready-to-stream video assets. Accepts both Guest and Subscriber tokens.",
)
def list_public_videos(
    current_subscriber: CurrentSubscriber,
    category: str | None = Query(None, description="Filter videos by category slug"),
    search: str | None = Query(None, description="Search title by substring"),
    sort: str | None = Query(
        "newest",
        description="Sort order: newest, oldest, popular (weighted: views + 3*likes), most_liked",
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return mobile_video_service.list_public_videos(
        creator_id=current_subscriber.get("creator_id"),
        category=category,
        search=search,
        sort=sort,
        page=page,
        limit=limit,
        subscriber_id=current_subscriber.get("user_id"),
    )


@router.get(
    "/continue-watching",
    response_model=PaginatedResponse[MobileVideoListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Continue Watching Feed",
    description="Retrieves a paginated list of published & ready video assets started but not completed by the authenticated subscriber.",
)
def list_continue_watching_videos(
    current_subscriber: CurrentSubscriber,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    return mobile_video_service.list_continue_watching_videos(
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
        page=page,
        limit=limit,
    )


@router.get(
    "/history",
    response_model=PaginatedResponse[MobileVideoListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Full Watch History",
    description="Retrieves a paginated list of all video assets watched by the authenticated subscriber.",
)
def list_watch_history(
    current_subscriber: CurrentSubscriber,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return mobile_video_service.list_watch_history(
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
        page=page,
        limit=limit,
    )


@router.delete(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Clear All Watch History",
    description="Deletes all watch history records for the authenticated subscriber.",
)
def clear_watch_history(current_subscriber: CurrentSubscriber):
    mobile_video_service.clear_watch_history(
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
    )
    return {"status": "success", "message": "Watch history cleared successfully"}


@router.delete(
    "/history/{video_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove Single Video from Watch History",
    description="Deletes a specific video from the authenticated subscriber's watch history and continue watching carousel.",
)
def remove_video_from_watch_history(
    video_id: int, current_subscriber: CurrentSubscriber
):
    mobile_video_service.remove_video_from_watch_history(
        video_id=video_id,
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
    )
    return {"status": "success", "message": "Video removed from watch history"}


@router.get(
    "/liked",
    response_model=PaginatedResponse[MobileVideoListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get My Liked Videos",
    description="Retrieves a paginated list of published & ready video assets liked by the authenticated subscriber.",
)
def list_subscriber_liked_videos(
    current_subscriber: CurrentSubscriber,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return mobile_video_service.list_subscriber_liked_videos(
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
        page=page,
        limit=limit,
    )


@router.get(
    "/saved",
    response_model=PaginatedResponse[MobileVideoListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get My Saved Videos (My Watchlist)",
    description="Retrieves a paginated list of published & ready video assets saved/bookmarked by the authenticated subscriber.",
)
def list_subscriber_saved_videos(
    current_subscriber: CurrentSubscriber,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return mobile_video_service.list_subscriber_saved_videos(
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
        page=page,
        limit=limit,
    )


@router.get(
    "/{video_id}",
    response_model=MobileVideoDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Video Streaming Details & Player Links",
    description="Retrieves detailed video metadata along with presigned adaptive HLS stream URLs, MP4 download URLs, captions, and dynamic is_liked & is_saved state. Strictly requires a full subscriber account.",
)
def get_video_details(video_id: int, current_subscriber: CurrentSubscriber):
    return mobile_video_service.get_video_details(
        video_id=video_id,
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
    )


@router.post(
    "/{video_id}/progress",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sync Watch Progress Heartbeat (HTTP 204)",
    description="High-frequency (10s timer) playback heartbeat sync for mobile player. Returns 204 No Content for 0-byte payload optimization.",
)
def sync_watch_progress(
    video_id: int,
    payload: MobileWatchProgressRequest,
    current_subscriber: CurrentSubscriber,
):
    if current_subscriber.get("role") != "subscriber":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber access required to sync watch progress",
        )
    mobile_video_service.update_watch_progress(
        video_id=video_id,
        subscriber_id=current_subscriber.get("user_id"),
        progress_seconds=payload.progress_seconds,
        creator_id=current_subscriber.get("creator_id"),
    )


@router.post(
    "/{video_id}/views",
    response_model=MobileViewCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Increment Video View Count",
    description="Atomically increments the watch view counter for a published video asset after zero-trust watch threshold verification.",
)
def record_video_view(video_id: int, current_subscriber: CurrentSubscriber):
    if current_subscriber.get("role") != "subscriber":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber access required to record views",
        )
    return mobile_video_service.record_video_view(
        video_id=video_id,
        subscriber_id=current_subscriber["user_id"],
        creator_id=current_subscriber.get("creator_id"),
    )


@router.post(
    "/{video_id}/like",
    response_model=MobileVideoLikeResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Subscriber Video Like",
    description="Toggles like state (like / unlike) for an authenticated subscriber on a published video asset.",
)
def toggle_video_like(video_id: int, current_subscriber: CurrentSubscriber):
    return mobile_video_service.toggle_video_like(
        video_id=video_id,
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
    )


@router.post(
    "/{video_id}/save",
    response_model=MobileVideoSaveResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Subscriber Video Save (Watchlist)",
    description="Toggles saved/bookmarked state (save / unsave) for an authenticated subscriber on a published video asset.",
)
def toggle_video_save(video_id: int, current_subscriber: CurrentSubscriber):
    return mobile_video_service.toggle_video_save(
        video_id=video_id,
        subscriber_id=current_subscriber.get("user_id"),
        creator_id=current_subscriber.get("creator_id"),
    )
