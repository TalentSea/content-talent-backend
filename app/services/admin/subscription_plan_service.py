import logging

from fastapi import HTTPException, status

from app.constants.plans import get_plan_features
from app.repositories.admin.subscription_plan_repository import (
    SubscriptionPlanRepository,
)
from app.schemas.admin.subscription_plan_schemas import (
    SubscriptionPlanItemResponse,
    SubscriptionPlanUpdateRequest,
)

logger = logging.getLogger(__name__)


class SubscriptionPlanService:
    """
    Business logic layer for Admin Subscription Plans management.
    Enforces strict two-tier OTT model with platform-governed technical features.
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
        reading the counter cache column active_subscribers in pure O(1) constant time (< 1ms)
        and attaching dynamic platform-governed features.
        """
        subs_count = getattr(plan, "active_subscribers", 0) or 0
        monthly_rev = round(subs_count * plan.final_price, 2)
        plan_type = getattr(plan, "plan_type", "with_ads") or "with_ads"
        features = get_plan_features(plan_type, plan.display_order)

        return SubscriptionPlanItemResponse(
            id=plan.id,
            plan_type=plan_type,
            name=plan.name,
            description=plan.description,
            base_price=plan.base_price,
            discount_percentage=plan.discount_percentage,
            final_price=plan.final_price,
            currency=plan.currency,
            billing_period_value=plan.billing_period_value,
            billing_period_unit=plan.billing_period_unit,
            features=features,
            badge_text=plan.badge_text,
            display_order=plan.display_order,
            active_subscribers=subs_count,
            monthly_revenue=monthly_rev,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    def list_plans(self, tenant_id: int) -> list[SubscriptionPlanItemResponse]:
        """
        Retrieves the fixed subscription plans for creator studio matching spec doc API 3.1.
        Executes in 1 single fast database query (< 1ms) with zero joins or counts.
        """
        plans = self.repo.get_plans_by_creator(tenant_id)
        return [self._map_to_item_response(p) for p in plans]

    def update_plan(
        self, tenant_id: int, plan_id: int, payload: SubscriptionPlanUpdateRequest
    ) -> SubscriptionPlanItemResponse:
        """
        Updates an existing subscription plan tier matching spec doc API 3.2.
        Only custom copy, pricing, and badge text may be modified.
        Features and technical tier parameters remain strictly platform-governed.
        """
        existing_plan = self.repo.get_plan_by_id(tenant_id, plan_id)
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan {plan_id} not found.",
            )

        if payload.name and self.repo.plan_name_exists(
            tenant_id, payload.name, exclude_id=plan_id
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
        if payload.badge_text is not None:
            update_dict["badge_text"] = (
                payload.badge_text.strip() if payload.badge_text else None
            )

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

        if not update_dict:
            return self._map_to_item_response(existing_plan)

        updated_plan = self.repo.update_plan(tenant_id, plan_id, update_dict)
        return self._map_to_item_response(updated_plan)
