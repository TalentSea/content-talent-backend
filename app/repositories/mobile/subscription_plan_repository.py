import logging

from peewee import PeeweeException

from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


class MobileSubscriptionPlanRepository:
    """
    Data access layer for Mobile Subscribers querying active subscription plans.
    """

    def get_active_plans(self, tenant_id: int) -> list[SubscriptionPlan]:
        """
        Retrieves all active plans for a creator studio ordered by display_order ascending.
        """
        try:
            return list(
                SubscriptionPlan.select()
                .where(SubscriptionPlan.tenant == tenant_id)
                .order_by(
                    SubscriptionPlan.display_order.asc(),
                    SubscriptionPlan.created_at.asc(),
                )
            )
        except PeeweeException as e:
            logger.error(
                "Error fetching active plans for mobile creator %s: %s", tenant_id, e
            )
            return []

    def get_plan_by_id(
        self, plan_id: int, tenant_id: int | None = None
    ) -> SubscriptionPlan | None:
        """
        Retrieves a subscription plan by ID scoped strictly to tenant_id if provided.
        """
        try:
            if tenant_id is not None:
                return SubscriptionPlan.get_or_none(
                    (SubscriptionPlan.id == plan_id)
                    & (SubscriptionPlan.tenant == tenant_id)
                )
            return SubscriptionPlan.get_or_none(SubscriptionPlan.id == plan_id)
        except PeeweeException as e:
            logger.error(
                "Error fetching subscription plan %s for tenant %s: %s",
                plan_id,
                tenant_id,
                e,
            )
            return None

