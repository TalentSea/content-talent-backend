from fastapi import APIRouter, Header, Request, status

from app.schemas.admin.video_schemas import BunnyWebhookPayload
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.admin.video_service import VideoService
from app.services.mobile.payment_service import MobilePaymentService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
video_service = VideoService()
payment_service = MobilePaymentService()


@router.post(
    "/bunny", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK
)
def handle_bunny_webhook(payload: BunnyWebhookPayload):
    """
    POST /api/v1/webhooks/bunny — Processes automated encoding state machine webhooks from Bunny Stream.
    Public unauthenticated callback endpoint for Bunny CDN webhooks.
    """
    return video_service.handle_bunny_webhook(payload)


@router.post(
    "/razorpay",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Razorpay Webhook Callback",
    description="Asynchronous server-to-server callback processing payment captures and failures as a fallback safety net.",
)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
):
    raw_body = await request.body()
    return payment_service.handle_webhook(raw_body, x_razorpay_signature)
