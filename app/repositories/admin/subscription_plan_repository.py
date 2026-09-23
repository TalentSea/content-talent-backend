import logging
from datetime import datetime, timezone

from peewee import PeeweeException, fn

from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionPlanRepository:
    """
    Data access layer for Admin Subscription Plans management.
    Enforces multi-tenant isolation on all queries.
    """

    def get_plans_by_creator(self, tenant_id: int) -> list[SubscriptionPlan]:
        """
        Retrieves all subscription plans for a tenant studio ordered by display_order ascending.
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
            logger.error("Error fetching plans for tenant %s: %s", tenant_id, e)
            return []

    def get_plan_by_id(self, tenant_id: int, plan_id: int) -> SubscriptionPlan | None:
        """
        Retrieves a single subscription plan by ID ensuring tenant studio ownership.
        """
        try:
            return (
                SubscriptionPlan.select()
                .where(
                    (SubscriptionPlan.id == plan_id)
                    & (SubscriptionPlan.tenant == tenant_id)
                )
                .first()
            )
        except PeeweeException as e:
            logger.error(
                "Error fetching plan %s for tenant %s: %s", plan_id, tenant_id, e
            )
            return None

    def plan_name_exists(
        self, tenant_id: int, name: str, exclude_id: int | None = None
    ) -> bool:
        """
        Checks if a plan with the same name already exists for this tenant.
        """
        try:
            query = SubscriptionPlan.select().where(
                (SubscriptionPlan.tenant == tenant_id)
                & (fn.LOWER(SubscriptionPlan.name) == name.strip().lower())
            )
            if exclude_id:
                query = query.where(SubscriptionPlan.id != exclude_id)
            return query.exists()
        except PeeweeException as e:
            logger.error("Error checking plan name existence: %s", e)
            return False

    def update_plan(
        self, tenant_id: int, plan_id: int, update_data: dict
    ) -> SubscriptionPlan | None:
        """
        Updates an existing subscription plan ensuring tenant ownership.
        """
        try:
            plan = self.get_plan_by_id(tenant_id, plan_id)
            if not plan:
                return None

            update_data["updated_at"] = datetime.now(timezone.utc)
            query = SubscriptionPlan.update(**update_data).where(
                (SubscriptionPlan.id == plan_id) & (SubscriptionPlan.tenant == tenant_id)
            )
            query.execute()
            return self.get_plan_by_id(tenant_id, plan_id)
        except PeeweeException as e:
            logger.error("Error updating plan %s: %s", plan_id, e)
            raise
