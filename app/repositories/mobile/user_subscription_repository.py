import logging
from datetime import datetime, timezone

from peewee import PeeweeException, fn

from app.database import db_proxy
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription

logger = logging.getLogger(__name__)


class UserSubscriptionRepository:
    """
    Data access layer for active subscriber access grants and plan entitlements.
    Follows Two-Pillar architecture:
    1. Pure read-only SQL entitlement checks (end_date > now()).
    2. Atomic background batch reconciliation for expired rows.
    """

    def get_active_subscription(
        self, user_id: int, creator_id: int
    ) -> UserSubscription | None:
        """
        Retrieves the currently active, unexpired subscription for a user under a specific creator.
        Pillar 1: Deterministic, read-only SQL entitlement check (end_date > now()).
        Pure read-only operation with zero write-locks or write-on-read side effects.
        """
        now = datetime.now(timezone.utc)
        try:
            return (
                UserSubscription.select(UserSubscription, SubscriptionPlan)
                .join(SubscriptionPlan)
                .where(
                    (UserSubscription.user == user_id)
                    & (UserSubscription.creator == creator_id)
                    & (UserSubscription.status == "active")
                    & (UserSubscription.end_date > now)
                )
                .order_by(UserSubscription.end_date.desc())
                .first()
            )
        except PeeweeException as err:
            logger.error(
                "Error querying active subscription for user %s, creator %s: %s",
                user_id,
                creator_id,
                err,
            )
            return None

    def expire_outdated_subscriptions(self) -> int:
        """
        Pillar 2: Batch-reconciles all past-due active subscriptions to 'expired' status.
        Executes within an atomic database transaction and keeps SubscriptionPlan.active_subscribers
        counter caches in sync.
        Returns the number of subscriptions transitioned to 'expired'.
        """
        now = datetime.now(timezone.utc)
        try:
            with db_proxy.atomic():
                # 1. Group past-due active subscriptions by plan to synchronize counters
                expired_counts = list(
                    UserSubscription.select(
                        UserSubscription.plan,
                        fn.COUNT(UserSubscription.id).alias("cnt"),
                    )
                    .where(
                        (UserSubscription.status == "active")
                        & (UserSubscription.end_date <= now)
                    )
                    .group_by(UserSubscription.plan)
                    .tuples()
                )

                if not expired_counts:
                    return 0

                # 2. Batch update status to 'expired'
                total_expired = (
                    UserSubscription.update(status="expired", updated_at=now)
                    .where(
                        (UserSubscription.status == "active")
                        & (UserSubscription.end_date <= now)
                    )
                    .execute()
                )

                # 3. Synchronize SubscriptionPlan.active_subscribers counter cache
                for plan_id, count in expired_counts:
                    plan = SubscriptionPlan.get_or_none(SubscriptionPlan.id == plan_id)
                    if plan:
                        plan.active_subscribers = max(
                            0, (plan.active_subscribers or 0) - count
                        )
                        plan.save()

                return total_expired
        except PeeweeException as err:
            logger.error("Error batch expiring outdated subscriptions: %s", err)
            return 0

    def get_subscription_by_payment(self, payment_id: int) -> UserSubscription | None:
        """
        Retrieves a subscription record originated by a specific payment ID.
        """
        try:
            return (
                UserSubscription.select(UserSubscription, SubscriptionPlan)
                .join(SubscriptionPlan)
                .where(UserSubscription.payment == payment_id)
                .first()
            )
        except PeeweeException as err:
            logger.error(
                "Error fetching subscription for payment %s: %s", payment_id, err
            )
            return None

    def create_subscription(
        self,
        user_id: int,
        creator_id: int,
        plan_id: int,
        payment_id: int | None,
        start_date: datetime,
        end_date: datetime,
    ) -> UserSubscription | None:
        """
        Creates an active user subscription record and returns eager-loaded entity with SubscriptionPlan.
        """
        try:
            created = UserSubscription.create(
                user=user_id,
                creator=creator_id,
                plan=plan_id,
                payment=payment_id,
                start_date=start_date,
                end_date=end_date,
                status="active",
            )
            return (
                UserSubscription.select(UserSubscription, SubscriptionPlan)
                .join(SubscriptionPlan)
                .where(UserSubscription.id == created.id)
                .first()
            )
        except PeeweeException as err:
            logger.error(
                "Error creating subscription for user %s, plan %s: %s",
                user_id,
                plan_id,
                err,
            )
            return None
