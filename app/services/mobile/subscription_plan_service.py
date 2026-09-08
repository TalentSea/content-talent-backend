import logging

from app.repositories.mobile.subscription_plan_repository import (
    MobileSubscriptionPlanRepository,
)
from app.schemas.mobile.subscription_plan_schemas import MobileSubscriptionPlanResponse

logger = logging.getLogger(__name__)


class MobileSubscriptionPlanService:
    """
    Business logic layer for Mobile Subscribers querying active subscription plans.
    """

    def __init__(self, repo: MobileSubscriptionPlanRepository | None = None) -> None:
        self.repo = repo or MobileSubscriptionPlanRepository()

    def list_active_plans(
        self, creator_id: int
    ) -> list[MobileSubscriptionPlanResponse]:
        """
        Retrieves active plans for mobile paywall checkout matching spec doc API 2.1.
        """
        plans = self.repo.get_active_plans(creator_id)
        return [
            MobileSubscriptionPlanResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                base_price=p.base_price,
                discount_percentage=p.discount_percentage,
                final_price=p.final_price,
                currency=p.currency,
                billing_period_value=p.billing_period_value,
                billing_period_unit=p.billing_period_unit,
                features=p.features or [],
                badge_text=p.badge_text,
                display_order=p.display_order,
            )
            for p in plans
        ]
