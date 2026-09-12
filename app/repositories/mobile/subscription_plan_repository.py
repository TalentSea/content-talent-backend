import logging

from peewee import PeeweeException

from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


class MobileSubscriptionPlanRepository:
    """
    Data access layer for Mobile Subscribers querying active subscription plans.
    """

    def get_active_plans(self, creator_id: int) -> list[SubscriptionPlan]:
        """
        Retrieves all active plans for a creator studio ordered by display_order ascending.
        """
        try:
            return list(
                SubscriptionPlan.select()
                .where(
                    (SubscriptionPlan.user == creator_id)
                    & (SubscriptionPlan.is_active == 1)
                )
                .order_by(
                    SubscriptionPlan.display_order.asc(),
                    SubscriptionPlan.created_at.asc(),
                )
            )
        except PeeweeException as e:
            logger.error(
                "Error fetching active plans for mobile creator %s: %s", creator_id, e
            )
            return []
