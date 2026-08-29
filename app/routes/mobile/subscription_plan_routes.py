from fastapi import APIRouter, status

from app.dependencies import CurrentSubscriber
from app.schemas.mobile.subscription_plan_schemas import MobileSubscriptionPlanResponse
from app.services.mobile.subscription_plan_service import MobileSubscriptionPlanService

router = APIRouter(prefix="/api/v1/mobile/plans", tags=["Mobile Subscription Plans"])
service = MobileSubscriptionPlanService()


@router.get(
    "",
    response_model=list[MobileSubscriptionPlanResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Mobile Subscription Plans Feed",
    description="Retrieves active subscription plans for the mobile paywall checkout screen ordered by display sequence. Accessible by Subscribers and Guest users.",
)
def list_mobile_subscription_plans(current_subscriber: CurrentSubscriber):
    creator_id = current_subscriber.get("creator_id")
    return service.list_active_plans(creator_id)
