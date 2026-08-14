from fastapi import APIRouter, status

from app.schemas.common_schemas import ActionSuccessResponse
from app.schemas.video_schemas import BunnyWebhookPayload
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
video_service = VideoService()


@router.post(
    "/bunny", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK
)
def handle_bunny_webhook(payload: BunnyWebhookPayload):
    """
    POST /api/v1/webhooks/bunny — Processes automated encoding state machine webhooks from Bunny Stream.
    Public unauthenticated callback endpoint for Bunny CDN webhooks.
    """
    return video_service.handle_bunny_webhook(payload)
