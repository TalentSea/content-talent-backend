import logging
from datetime import datetime, timezone
from peewee import IntegrityError, PeeweeException, fn

from app.database import db_proxy
from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionPlanRepository:
    """
    Data access layer for Admin Subscription Plans management.
    Enforces multi-tenant creator isolation on all queries.
    """

    def get_plans_by_creator(self, creator_id: int) -> list[SubscriptionPlan]:
        """
        Retrieves all subscription plans for a creator studio ordered by display_order ascending.
        """
        try:
            return list(
                SubscriptionPlan.select()
                .where(SubscriptionPlan.user == creator_id)
                .order_by(SubscriptionPlan.display_order.asc(), SubscriptionPlan.created_at.asc())
            )
        except PeeweeException as e:
            logger.error("Error fetching plans for creator %s: %s", creator_id, e)
            return []

    def get_plan_by_id(self, creator_id: int, plan_id: int) -> SubscriptionPlan | None:
        """
        Retrieves a single subscription plan by ID ensuring creator studio ownership.
        """
        try:
            return (
                SubscriptionPlan.select()
                .where(
                    (SubscriptionPlan.id == plan_id)
                    & (SubscriptionPlan.user == creator_id)
                )
                .first()
            )
        except PeeweeException as e:
            logger.error("Error fetching plan %s for creator %s: %s", plan_id, creator_id, e)
            return None

    def plan_name_exists(
        self, creator_id: int, name: str, exclude_id: int | None = None
    ) -> bool:
        """
        Checks if a plan with the same name already exists for this creator.
        """
        try:
            query = SubscriptionPlan.select().where(
                (SubscriptionPlan.user == creator_id)
                & (fn.LOWER(SubscriptionPlan.name) == name.strip().lower())
            )
            if exclude_id:
                query = query.where(SubscriptionPlan.id != exclude_id)
            return query.exists()
        except PeeweeException as e:
            logger.error("Error checking plan name existence: %s", e)
            return False

    def get_next_display_order(self, creator_id: int) -> int:
        """
        Calculates next display order sequence number for a new plan.
        """
        try:
            max_order = (
                SubscriptionPlan.select(fn.MAX(SubscriptionPlan.display_order))
                .where(SubscriptionPlan.user == creator_id)
                .scalar()
            )
            return (max_order or 0) + 1
        except PeeweeException:
            return 1

    def create_plan(self, creator_id: int, data: dict) -> SubscriptionPlan:
        """
        Creates a new subscription plan record bound to creator studio.
        """
        try:
            data["user"] = creator_id
            if "display_order" not in data or data["display_order"] is None:
                data["display_order"] = self.get_next_display_order(creator_id)
            return SubscriptionPlan.create(**data)
        except IntegrityError as e:
            logger.error("Integrity error creating subscription plan: %s", e)
            raise

    def update_plan(
        self, creator_id: int, plan_id: int, update_data: dict
    ) -> SubscriptionPlan | None:
        """
        Updates an existing subscription plan ensuring creator ownership.
        """
        try:
            plan = self.get_plan_by_id(creator_id, plan_id)
            if not plan:
                return None

            update_data["updated_at"] = datetime.now(timezone.utc)
            query = SubscriptionPlan.update(**update_data).where(
                (SubscriptionPlan.id == plan_id) & (SubscriptionPlan.user == creator_id)
            )
            query.execute()
            return self.get_plan_by_id(creator_id, plan_id)
        except PeeweeException as e:
            logger.error("Error updating plan %s: %s", plan_id, e)
            raise

    def delete_plan(self, creator_id: int, plan_id: int) -> bool:
        """
        Deletes a subscription plan for creator_id and automatically compacts
        remaining plans' display_order to maintain a continuous 1..N sequence.
        """
        try:
            plan = self.get_plan_by_id(creator_id, plan_id)
            if not plan:
                return False

            deleted_order = plan.display_order
            with db_proxy.atomic():
                SubscriptionPlan.delete().where(
                    (SubscriptionPlan.id == plan_id)
                    & (SubscriptionPlan.user == creator_id)
                ).execute()

                # Compact gap: shift down all plans that had a higher display_order
                SubscriptionPlan.update(
                    display_order=SubscriptionPlan.display_order - 1,
                    updated_at=datetime.now(timezone.utc),
                ).where(
                    (SubscriptionPlan.user == creator_id)
                    & (SubscriptionPlan.display_order > deleted_order)
                ).execute()

            return True
        except PeeweeException as e:
            logger.error("Error deleting plan %s: %s", plan_id, e)
            return False

    def toggle_active(self, creator_id: int, plan_id: int) -> SubscriptionPlan | None:
        """
        Toggles is_active boolean value on a plan.
        """
        try:
            plan = self.get_plan_by_id(creator_id, plan_id)
            if not plan:
                return None

            new_status = not plan.is_active
            now_utc = datetime.now(timezone.utc)
            SubscriptionPlan.update(is_active=new_status, updated_at=now_utc).where(
                (SubscriptionPlan.id == plan_id) & (SubscriptionPlan.user == creator_id)
            ).execute()

            plan.is_active = new_status
            plan.updated_at = now_utc
            return plan
        except PeeweeException as e:
            logger.error("Error toggling active status on plan %s: %s", plan_id, e)
            return None

    def reorder_plans(self, creator_id: int, plan_ids: list[int]) -> bool:
        """
        Atomically updates the display_order of plans based on the given IDs sequence.
        """
        try:
            # 1. Verify all plan IDs belong to this creator
            existing_ids = set(
                SubscriptionPlan.select(SubscriptionPlan.id)
                .where(
                    (SubscriptionPlan.user == creator_id)
                    & (SubscriptionPlan.id.in_(plan_ids))
                )
                .tuples()
            )
            existing_id_set = {row[0] for row in existing_ids}

            if len(existing_id_set) != len(plan_ids):
                return False

            with db_proxy.atomic():
                for idx, pid in enumerate(plan_ids, start=1):
                    SubscriptionPlan.update(
                        display_order=idx, updated_at=datetime.now(timezone.utc)
                    ).where(
                        (SubscriptionPlan.id == pid)
                        & (SubscriptionPlan.user == creator_id)
                    ).execute()
            return True
        except PeeweeException as e:
            logger.error("Error reordering plans for creator %s: %s", creator_id, e)
            return False
