from fastapi import APIRouter, status

from app.dependencies import CurrentSubscriber
from app.schemas.mobile.payment_schemas import SubscriptionStatusResponse
from app.services.mobile.payment_service import MobilePaymentService

router = APIRouter(prefix="/api/v1/mobile/subscriptions", tags=["Mobile Subscriptions"])
payment_service = MobilePaymentService()


@router.get(
    "/me",
    response_model=SubscriptionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Active Subscription Status",
    description="Retrieves active membership entitlement status and remaining days for the current subscriber.",
)
def get_current_subscription(current_subscriber: CurrentSubscriber):
    return payment_service.get_subscription_status(current_subscriber)
