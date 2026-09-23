from fastapi import APIRouter, status

from app.dependencies import CurrentAdmin
from app.schemas.admin.subscription_plan_schemas import (
    SubscriptionPlanItemResponse,
    SubscriptionPlanUpdateRequest,
)
from app.services.admin.subscription_plan_service import SubscriptionPlanService

router = APIRouter(prefix="/api/v1/admin/plans", tags=["Admin Subscription Plans"])
service = SubscriptionPlanService()


@router.get(
    "",
    response_model=list[SubscriptionPlanItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List Creator Subscription Plans",
    description="Retrieves the 2 fixed subscription plans owned by the creator studio ordered by display_order ascending, enriched with built-in feature lists and live subscriber/revenue metrics.",
)
def list_subscription_plans(current_user: CurrentAdmin):
    return service.list_plans(current_user["tenant_id"])


@router.put(
    "/{plan_id}",
    response_model=SubscriptionPlanItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Subscription Plan Pricing & Copy",
    description="Saves creator customizations (name, description, pricing, discount, badge text) for an existing plan tier. Technical features and entitlements remain platform-governed.",
)
def update_subscription_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdateRequest,
    current_user: CurrentAdmin,
):
    return service.update_plan(current_user["tenant_id"], plan_id, payload)
