import logging

from app.constants.plans import get_plan_features
from app.repositories.admin.subscription_plan_repository import (
    SubscriptionPlanRepository,
)
from app.schemas.mobile.subscription_plan_schemas import MobileSubscriptionPlanResponse

logger = logging.getLogger(__name__)


class MobileSubscriptionPlanService:
    """
    Business logic layer for Mobile Subscribers querying active subscription plans.
    """

    def __init__(self, repo: SubscriptionPlanRepository | None = None) -> None:
        self.repo = repo or SubscriptionPlanRepository()

    def list_active_plans(
        self, tenant_id: int
    ) -> list[MobileSubscriptionPlanResponse]:
        """
        Retrieves active plans for mobile paywall checkout matching spec doc API 2.1.
        Enriched with dynamic built-in platform features.
        """
        plans = self.repo.get_plans_by_creator(tenant_id)
        return [
            MobileSubscriptionPlanResponse(
                id=p.id,
                plan_type=getattr(p, "plan_type", "with_ads") or "with_ads",
                name=p.name,
                description=p.description,
                base_price=p.base_price,
                discount_percentage=p.discount_percentage,
                final_price=p.final_price,
                currency=p.currency,
                billing_period_value=p.billing_period_value,
                billing_period_unit=p.billing_period_unit,
                features=get_plan_features(
                    getattr(p, "plan_type", "with_ads"), p.display_order
                ),
                badge_text=p.badge_text,
                display_order=p.display_order,
            )
            for p in plans
        ]
