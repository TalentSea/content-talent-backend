from fastapi import APIRouter, Depends, Query, status
from app.dependencies import get_current_user
from app.schemas.video_schemas import (
    VideoInitiateRequest,
    VideoInitiateResponse,
    VideoResponse,
    VideoUpdateRequest,
    ThumbnailUploadUrlRequest,
    ThumbnailUploadUrlResponse,
    SelectMainThumbnailRequest,
    DeleteThumbnailRequest,
    BunnyWebhookPayload
)
from app.schemas.common_schemas import PaginatedResponse

router = APIRouter(prefix="/api/v1/videos", tags=["Videos"])

@router.post("/initiate", response_model=VideoInitiateResponse, status_code=status.HTTP_201_CREATED)
def initiate_video(payload: VideoInitiateRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/videos/initiate — Initiates video upload session and returns TUS presigned signature.
    """
    pass

@router.post("/webhooks/bunny", status_code=status.HTTP_200_OK)
def handle_webhook(payload: BunnyWebhookPayload):
    """
    POST /api/v1/webhooks/bunny — Handles automated state machine webhooks from Bunny Stream.
    """
    pass

@router.get("", response_model=PaginatedResponse[VideoResponse], status_code=status.HTTP_200_OK)
def list_videos(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/videos — Retrieves a paginated list of videos uploaded by the authenticated creator.
    """
    pass

@router.get("/{video_id}", response_model=VideoResponse, status_code=status.HTTP_200_OK)
def get_video_details(video_id: int, current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/videos/{video_id} — Retrieves video details and triggers live encoding status sync if processing.
    """
    pass

@router.patch("/{video_id}", response_model=VideoResponse, status_code=status.HTTP_200_OK)
def update_video_metadata(video_id: int, payload: VideoUpdateRequest, current_user: dict = Depends(get_current_user)):
    """
    PATCH /api/v1/videos/{video_id} — Updates textual metadata fields (title, description, category, tags).
    """
    pass

@router.post("/{video_id}/thumbnails/upload-url", response_model=ThumbnailUploadUrlResponse, status_code=status.HTTP_200_OK)
def request_thumbnail_upload_url(video_id: int, payload: ThumbnailUploadUrlRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/videos/{video_id}/thumbnails/upload-url — Generates presigned write-only upload URL for slot 0, 1, or 2.
    """
    pass

@router.patch("/{video_id}/thumbnails/select-main", response_model=VideoResponse, status_code=status.HTTP_200_OK)
def select_main_thumbnail(video_id: int, payload: SelectMainThumbnailRequest, current_user: dict = Depends(get_current_user)):
    """
    PATCH /api/v1/videos/{video_id}/thumbnails/select-main — Promotes alt thumbnail to main cover and swaps previous main cover into alt array.
    """
    pass

@router.delete("/{video_id}/thumbnails", response_model=VideoResponse, status_code=status.HTTP_200_OK)
def delete_thumbnail(video_id: int, payload: DeleteThumbnailRequest, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/videos/{video_id}/thumbnails — Deletes alternative backup thumbnail permanently from cloud storage and DB.
    """
    pass

@router.delete("/{video_id}", status_code=status.HTTP_200_OK)
def delete_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """
    DELETE /api/v1/videos/{video_id} — Deletes video asset from database and Bunny Stream container.
    """
    pass
