import logging

from fastapi import HTTPException, status

from app.repositories.admin.subscription_plan_repository import (
    SubscriptionPlanRepository,
)
from app.schemas.admin.subscription_plan_schemas import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanItemResponse,
    SubscriptionPlanReorderRequest,
    SubscriptionPlanToggleActiveResponse,
    SubscriptionPlanUpdateRequest,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse

logger = logging.getLogger(__name__)


class SubscriptionPlanService:
    """
    Business logic layer for Admin Subscription Plans management.
    """

    def __init__(self, repo: SubscriptionPlanRepository | None = None) -> None:
        self.repo = repo or SubscriptionPlanRepository()

    def _calculate_final_price(
        self, base_price: float, discount_percentage: float
    ) -> float:
        """
        Calculates final charge price after discount percentage:
        final_price = round(base_price * (1 - discount_percentage / 100), 2)
        """
        if discount_percentage <= 0:
            return round(base_price, 2)
        discount_factor = 1.0 - (discount_percentage / 100.0)
        return round(max(0.0, base_price * discount_factor), 2)

    def _map_to_item_response(self, plan) -> SubscriptionPlanItemResponse:
        """
        Maps a SubscriptionPlan Peewee ORM model to SubscriptionPlanItemResponse DTO
        reading the counter cache column active_subscribers in pure O(1) constant time (< 1ms).
        """
        subs_count = getattr(plan, "active_subscribers", 0) or 0
        monthly_rev = round(subs_count * plan.final_price, 2)

        return SubscriptionPlanItemResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            base_price=plan.base_price,
            discount_percentage=plan.discount_percentage,
            final_price=plan.final_price,
            currency=plan.currency,
            billing_period_value=plan.billing_period_value,
            billing_period_unit=plan.billing_period_unit,
            features=plan.features or [],
            badge_text=plan.badge_text,
            is_active=plan.is_active,
            display_order=plan.display_order,
            active_subscribers=subs_count,
            monthly_revenue=monthly_rev,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    def list_plans(self, creator_id: int) -> list[SubscriptionPlanItemResponse]:
        """
        Retrieves all subscription plans for creator studio matching spec doc API 3.1.
        Executes in 1 single fast database query (< 1ms) with zero joins or counts.
        """
        plans = self.repo.get_plans_by_creator(creator_id)
        return [self._map_to_item_response(p) for p in plans]

    def create_plan(
        self, creator_id: int, payload: SubscriptionPlanCreateRequest
    ) -> SubscriptionPlanItemResponse:
        """
        Creates a new subscription plan tier matching spec doc API 3.2.
        """
        # Validate unique plan name per creator
        if self.repo.plan_name_exists(creator_id, payload.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription plan with name '{payload.name}' already exists for this creator studio.",
            )

        final_price = self._calculate_final_price(
            payload.base_price, payload.discount_percentage
        )

        plan_data = {
            "name": payload.name.strip(),
            "description": payload.description.strip() if payload.description else None,
            "base_price": round(payload.base_price, 2),
            "discount_percentage": round(payload.discount_percentage, 2),
            "final_price": final_price,
            "currency": "INR",
            "billing_period_value": payload.billing_period_value,
            "billing_period_unit": payload.billing_period_unit.strip().lower(),
            "features": [f.strip() for f in payload.features if f.strip()],
            "badge_text": payload.badge_text.strip() if payload.badge_text else None,
            "is_active": payload.is_active,
        }

        created_plan = self.repo.create_plan(creator_id, plan_data)
        return self._map_to_item_response(created_plan)

    def update_plan(
        self, creator_id: int, plan_id: int, payload: SubscriptionPlanUpdateRequest
    ) -> SubscriptionPlanItemResponse:
        """
        Updates an existing subscription plan tier matching spec doc API 3.3.
        """
        existing_plan = self.repo.get_plan_by_id(creator_id, plan_id)
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan {plan_id} not found.",
            )

        if payload.name and self.repo.plan_name_exists(
            creator_id, payload.name, exclude_id=plan_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription plan with name '{payload.name}' already exists.",
            )

        update_dict = {}
        if payload.name is not None:
            update_dict["name"] = payload.name.strip()
        if payload.description is not None:
            update_dict["description"] = (
                payload.description.strip() if payload.description else None
            )
        if payload.billing_period_value is not None:
            update_dict["billing_period_value"] = payload.billing_period_value
        if payload.billing_period_unit is not None:
            update_dict["billing_period_unit"] = (
                payload.billing_period_unit.strip().lower()
            )
        if payload.features is not None:
            update_dict["features"] = [f.strip() for f in payload.features if f.strip()]
        if payload.badge_text is not None:
            update_dict["badge_text"] = (
                payload.badge_text.strip() if payload.badge_text else None
            )
        if payload.is_active is not None:
            update_dict["is_active"] = payload.is_active

        # Recalculate price if either base_price or discount_percentage is updated
        new_base_price = (
            payload.base_price
            if payload.base_price is not None
            else existing_plan.base_price
        )
        new_discount = (
            payload.discount_percentage
            if payload.discount_percentage is not None
            else existing_plan.discount_percentage
        )

        if payload.base_price is not None or payload.discount_percentage is not None:
            update_dict["base_price"] = round(new_base_price, 2)
            update_dict["discount_percentage"] = round(new_discount, 2)
            update_dict["final_price"] = self._calculate_final_price(
                new_base_price, new_discount
            )

        updated_plan = self.repo.update_plan(creator_id, plan_id, update_dict)
        return self._map_to_item_response(updated_plan)

    def delete_plan(self, creator_id: int, plan_id: int) -> ActionSuccessResponse:
        """
        Deletes a subscription plan tier matching spec doc API 3.4.
        """
        existing_plan = self.repo.get_plan_by_id(creator_id, plan_id)
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan {plan_id} not found.",
            )

        success = self.repo.delete_plan(creator_id, plan_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete subscription plan.",
            )

        return ActionSuccessResponse(
            status="success",
            message=f"Subscription plan {plan_id} deleted successfully",
        )

    def toggle_active_status(
        self, creator_id: int, plan_id: int
    ) -> SubscriptionPlanToggleActiveResponse:
        """
        Toggles is_active status of a plan matching spec doc API 3.5.
        """
        updated_plan = self.repo.toggle_active(creator_id, plan_id)
        if not updated_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan {plan_id} not found.",
            )

        return SubscriptionPlanToggleActiveResponse(
            id=updated_plan.id,
            name=updated_plan.name,
            is_active=updated_plan.is_active,
            updated_at=updated_plan.updated_at,
        )

    def reorder_plans(
        self, creator_id: int, payload: SubscriptionPlanReorderRequest
    ) -> ActionSuccessResponse:
        """
        Batch reorders plan cards matching spec doc API 3.6.
        """
        success = self.repo.reorder_plans(creator_id, payload.ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more plan IDs do not exist or belong to another creator studio.",
            )

        return ActionSuccessResponse(
            status="success",
            message="Subscription plan order updated",
        )
