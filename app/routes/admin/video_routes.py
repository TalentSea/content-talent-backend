from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, status

from app.dependencies import get_current_user
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
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/v1/admin/videos", tags=["Admin Videos"])
video_service = VideoService()

@router.post("/initiate", response_model=VideoInitiateResponse, status_code=status.HTTP_201_CREATED)
def initiate_video(payload: VideoInitiateRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/videos/initiate — Initiates a video upload container on Bunny Stream and returns TUS presigned signature.
    """
    return video_service.initiate_video_upload(current_user["user_id"], payload)

@router.post("/webhooks/bunny", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def handle_webhook(payload: BunnyWebhookPayload):
    """
    POST /api/v1/webhooks/bunny — Processes automated encoding state machine webhooks from Bunny Stream.
    """
    return video_service.handle_bunny_webhook(payload)

@router.get("", response_model=PaginatedResponse[VideoListItemResponse], status_code=status.HTTP_200_OK)
def list_videos(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by state: published, draft, scheduled"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    search: Optional[str] = Query(None, description="Search video titles by substring"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, oldest, views, title"),
    date_from: Optional[str] = Query(None, alias="dateFrom", description="Filter creation start date (ISO string)"),
    date_to: Optional[str] = Query(None, alias="dateTo", description="Filter creation end date (ISO string)"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/admin/videos — Retrieves a paginated, filterable list of uploaded videos belonging to the authenticated creator.
    """
    return video_service.list_user_videos(
        user_id=current_user["user_id"],
        status_filter=status_filter,
        category=category,
        search=search,
        sort=sort,
        date_from_str=date_from,
        date_to_str=date_to,
        page=page,
        limit=limit
    )

@router.get("/{video_id}", response_model=VideoResponse, status_code=status.HTTP_200_OK)
def get_video_details(video_id: int, current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/admin/videos/{video_id} — Retrieves single video details and triggers live encoding status sync if ENCODING.
    """
    return video_service.get_video_details(current_user["user_id"], video_id)

@router.patch("/{video_id}", response_model=VideoUpdateResponse, status_code=status.HTTP_200_OK)
def update_video_metadata(video_id: int, payload: VideoUpdateRequest, current_user: dict = Depends(get_current_user)):
    """
    PATCH /api/v1/admin/videos/{video_id} — Updates textual metadata fields (title, description, category, tags).
    """
    return video_service.update_video_metadata(current_user["user_id"], video_id, payload)

@router.post("/{video_id}/thumbnails/upload", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def upload_thumbnail(video_id: int, slot: int = Query(0, ge=0, le=2), file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/videos/{video_id}/thumbnails/upload?slot=0 — Uploads cover image binary via server proxy.
    """
    return video_service.upload_thumbnail_image(current_user["user_id"], video_id, slot=slot, file=file)

@router.patch("/{video_id}/thumbnails/select-main", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def select_main_thumbnail(video_id: int, payload: SelectMainThumbnailRequest, current_user: dict = Depends(get_current_user)):
    """
    PATCH /api/v1/admin/videos/{video_id}/thumbnails/select-main — Promotes alt thumbnail to primary cover image.
    """
    return video_service.select_main_thumbnail(current_user["user_id"], video_id, payload)

@router.delete("/{video_id}/thumbnails", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def delete_thumbnail(video_id: int, payload: DeleteThumbnailRequest, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/admin/videos/{video_id}/thumbnails — Deletes alternative backup thumbnail permanently from cloud storage and DB.
    """
    return video_service.delete_alternative_thumbnail(current_user["user_id"], video_id, payload)

@router.delete("/{video_id}", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def delete_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/admin/videos/{video_id} — Deletes a single video asset from database and Bunny Stream container.
    """
    return video_service.delete_video_asset(current_user["user_id"], video_id)

@router.post("/bulk-delete", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def bulk_delete_videos(payload: BulkDeleteVideosRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/videos/bulk-delete — Deletes multiple video assets in a single batch operation.
    """
    return video_service.bulk_delete_videos(current_user["user_id"], payload)

@router.post("/{video_id}/publish", response_model=VideoPublishResponse, status_code=status.HTTP_200_OK)
def publish_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/videos/{video_id}/publish — Publishes a video asset immediately.
    """
    return video_service.publish_video_immediately(current_user["user_id"], video_id)

@router.post("/{video_id}/schedule", response_model=VideoScheduleResponse, status_code=status.HTTP_200_OK)
def schedule_video(video_id: int, payload: VideoScheduleRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/admin/videos/{video_id}/schedule — Schedules a video asset for future publication.
    """
    return video_service.schedule_video_publication(current_user["user_id"], video_id, payload)
