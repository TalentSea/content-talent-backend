from fastapi import APIRouter, status

from app.dependencies import CurrentAdmin
from app.schemas.admin.subscription_plan_schemas import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanItemResponse,
    SubscriptionPlanReorderRequest,
    SubscriptionPlanToggleActiveResponse,
    SubscriptionPlanUpdateRequest,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.admin.subscription_plan_service import SubscriptionPlanService

router = APIRouter(prefix="/api/v1/admin/plans", tags=["Admin Subscription Plans"])
service = SubscriptionPlanService()


@router.get(
    "",
    response_model=list[SubscriptionPlanItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List Creator Subscription Plans",
    description="Retrieves all subscription plans owned by the creator studio ordered by display_order ascending, enriched with live subscriber and revenue metrics.",
)
def list_subscription_plans(current_user: CurrentAdmin):
    return service.list_plans(current_user["user_id"])


@router.post(
    "",
    response_model=SubscriptionPlanItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subscription Plan",
    description="Creates a new subscription plan tier with base price, discount %, interval period, and feature checklist.",
)
def create_subscription_plan(
    payload: SubscriptionPlanCreateRequest, current_user: CurrentAdmin
):
    return service.create_plan(current_user["user_id"], payload)


@router.put(
    "/reorder",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Reorder Plan Display Order",
    description="Atomically updates the display_order sequence for subscription plan cards on the dashboard grid.",
)
def reorder_subscription_plans(
    payload: SubscriptionPlanReorderRequest, current_user: CurrentAdmin
):
    return service.reorder_plans(current_user["user_id"], payload)


@router.put(
    "/{plan_id}",
    response_model=SubscriptionPlanItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Subscription Plan",
    description="Updates an existing subscription plan tier from the Edit modal form.",
)
def update_subscription_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdateRequest,
    current_user: CurrentAdmin,
):
    return service.update_plan(current_user["user_id"], plan_id, payload)


@router.delete(
    "/{plan_id}",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Subscription Plan",
    description="Deletes a subscription plan tier belonging to the creator studio.",
)
def delete_subscription_plan(plan_id: int, current_user: CurrentAdmin):
    return service.delete_plan(current_user["user_id"], plan_id)


@router.patch(
    "/{plan_id}/toggle-active",
    response_model=SubscriptionPlanToggleActiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Plan Active Status",
    description="Quick toggles the is_active visibility status (true/false) on a subscription plan card.",
)
def toggle_plan_active_status(plan_id: int, current_user: CurrentAdmin):
    return service.toggle_active_status(current_user["user_id"], plan_id)
