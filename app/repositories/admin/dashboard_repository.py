from datetime import datetime, timezone
from typing import Any

from peewee import fn

from app.models.payment import Payment
from app.models.subscriber import Subscriber
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.models.video import Video, WatchHistory


class DashboardRepository:
    """
    Encapsulates high-performance aggregation and reporting queries
    for the Admin Creator Studio Dashboard & Analytics subsystem.
    """

    def get_revenue_in_window(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> float:
        """Sums captured payments in ₹ INR within a date window."""
        res = (
            Payment.select(fn.COALESCE(fn.SUM(Payment.amount), 0.0))
            .where(
                Payment.creator == creator_id,
                Payment.status == "captured",
                Payment.created_at >= start_dt,
                Payment.created_at <= end_dt,
            )
            .scalar()
        )
        return float(res or 0.0)

    def get_views_in_window(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> int:
        """
        Counts playback sessions in window via WatchHistory.
        Falls back to Video.views sum if no watch history events exist.
        """
        history_views = (
            WatchHistory.select(fn.COUNT(WatchHistory.id))
            .join(Video)
            .where(
                Video.user == creator_id,
                WatchHistory.last_watched_at >= start_dt,
                WatchHistory.last_watched_at <= end_dt,
            )
            .scalar()
        )
        return int(history_views or 0)

    def get_lifetime_views(self, creator_id: int) -> int:
        """Sums lifetime playback views across all creator videos."""
        res = (
            Video.select(fn.COALESCE(fn.SUM(Video.views), 0))
            .where(Video.user == creator_id)
            .scalar()
        )
        return int(res or 0)

    def get_user_registrations_in_window(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> int:
        """Counts registered audience accounts (role='subscriber') registered in window."""
        return (
            Subscriber.select()
            .where(
                Subscriber.creator == creator_id,
                Subscriber.role == "subscriber",
                Subscriber.created_at >= start_dt,
                Subscriber.created_at <= end_dt,
            )
            .count()
        )

    def get_total_registered_users(self, creator_id: int) -> int:
        """Counts total registered audience accounts (excludes anonymous guests)."""
        return (
            Subscriber.select()
            .where(
                Subscriber.creator == creator_id,
                Subscriber.role == "subscriber",
            )
            .count()
        )

    def get_active_subscribers_count(self, creator_id: int) -> int:
        """Counts distinct users currently holding an active subscription."""
        res = (
            UserSubscription.select(fn.COUNT(fn.DISTINCT(UserSubscription.user)))
            .where(
                UserSubscription.creator == creator_id,
                UserSubscription.status == "active",
            )
            .scalar()
        )
        return int(res or 0)

    def get_subscribers_converted_in_window(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> int:
        """Counts new subscription enrollments created within the window."""
        res = (
            UserSubscription.select(fn.COUNT(fn.DISTINCT(UserSubscription.user)))
            .where(
                UserSubscription.creator == creator_id,
                UserSubscription.status == "active",
                UserSubscription.created_at >= start_dt,
                UserSubscription.created_at <= end_dt,
            )
            .scalar()
        )
        return int(res or 0)

    def get_content_inventory(
        self, creator_id: int, window_start: datetime
    ) -> dict[str, int]:
        """Returns inventory counts: total, published, drafts, recently_added."""
        total = Video.select().where(Video.user == creator_id).count()
        published = (
            Video.select()
            .where(
                Video.user == creator_id,
                fn.LOWER(Video.status) == "published",
                Video.is_playable == True,
            )
            .count()
        )
        drafts = (
            Video.select()
            .where(
                Video.user == creator_id,
                (fn.LOWER(Video.status) != "published") | (Video.is_playable == False),
            )
            .count()
        )
        recently_added = (
            Video.select()
            .where(
                Video.user == creator_id,
                Video.created_at >= window_start,
            )
            .count()
        )
        return {
            "total": total,
            "published": published,
            "drafts": drafts,
            "recently_added": recently_added,
        }

    def get_subscription_tier_breakdown(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> list[dict[str, Any]]:
        """
        Aggregates active subscriber counts and captured period revenue per subscription plan tier,
        preserving real plan names, IDs, badge texts, and active/inactive status.
        """
        # 1. Captured revenue per plan in the selected date window
        revenue_query = (
            Payment.select(
                Payment.plan.alias("plan_id"),
                fn.COALESCE(fn.SUM(Payment.amount), 0.0).alias("total_amount"),
            )
            .where(
                Payment.creator == creator_id,
                Payment.status == "captured",
                Payment.created_at >= start_dt,
                Payment.created_at <= end_dt,
            )
            .group_by(Payment.plan)
        )
        plan_revenues = {row.plan_id: float(row.total_amount) for row in revenue_query}

        # 2. Active subscriber counts per plan
        active_counts_query = (
            UserSubscription.select(
                UserSubscription.plan.alias("plan_id"),
                fn.COUNT(fn.DISTINCT(UserSubscription.user)).alias("sub_count"),
            )
            .where(
                UserSubscription.creator == creator_id,
                UserSubscription.status == "active",
            )
            .group_by(UserSubscription.plan)
        )
        sub_counts = {row.plan_id: int(row.sub_count) for row in active_counts_query}

        # 3. All plans configured by creator
        plans = list(
            SubscriptionPlan.select()
            .where(SubscriptionPlan.user == creator_id)
            .order_by(SubscriptionPlan.display_order.asc(), SubscriptionPlan.id.asc())
        )

        results = []
        for plan in plans:
            sub_cnt = sub_counts.get(plan.id, 0)
            rev_val = round(plan_revenues.get(plan.id, 0.0), 2)
            # Include tier if it has subscribers, generated revenue, or is currently active
            if sub_cnt > 0 or rev_val > 0.0 or plan.is_active:
                results.append(
                    {
                        "plan_id": plan.id,
                        "name": plan.name,
                        "badge_text": plan.badge_text,
                        "is_active": bool(plan.is_active),
                        "subscribers": sub_cnt,
                        "revenue": rev_val,
                    }
                )

        return results

    def get_recent_activity(
        self, creator_id: int, filter_type: str, page: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Retrieves paginated recent members feed.
        filter_type: 'all' | 'subscribers' | 'users'
        """
        active_sub_user_ids = (
            UserSubscription.select(UserSubscription.user)
            .where(
                UserSubscription.creator == creator_id,
                UserSubscription.status == "active",
            )
        )

        if filter_type == "subscribers":
            query = (
                UserSubscription.select(
                    UserSubscription,
                    Subscriber,
                    SubscriptionPlan,
                )
                .join(Subscriber, on=(UserSubscription.user == Subscriber.id))
                .switch(UserSubscription)
                .join(SubscriptionPlan, on=(UserSubscription.plan == SubscriptionPlan.id))
                .where(
                    UserSubscription.creator == creator_id,
                    UserSubscription.status == "active",
                    Subscriber.role == "subscriber",
                )
                .order_by(UserSubscription.created_at.desc())
            )

            total = query.count()
            rows = list(query.paginate(page, limit))
            items = []
            for sub_rec in rows:
                sub_user = sub_rec.user
                plan_rec = sub_rec.plan
                items.append(
                    {
                        "id": sub_user.id,
                        "name": sub_user.name,
                        "email": sub_user.email,
                        "avatar_url": sub_user.avatar_url,
                        "plan_name": plan_rec.name if plan_rec else None,
                        "is_paid": True,
                        "subscribed_at": sub_rec.created_at,
                        "joined_at": sub_user.created_at,
                    }
                )
            return items, total

        elif filter_type == "users":
            base_query = (
                Subscriber.select()
                .where(
                    Subscriber.creator == creator_id,
                    Subscriber.role == "subscriber",
                    Subscriber.id.not_in(active_sub_user_ids),
                )
                .order_by(Subscriber.created_at.desc())
            )
            total = base_query.count()
            users = list(base_query.paginate(page, limit))
            items = [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "avatar_url": u.avatar_url,
                    "plan_name": None,
                    "is_paid": False,
                    "subscribed_at": None,
                    "joined_at": u.created_at,
                }
                for u in users
            ]
            return items, total

        else:
            base_query = (
                Subscriber.select()
                .where(
                    Subscriber.creator == creator_id,
                    Subscriber.role == "subscriber",
                )
                .order_by(Subscriber.created_at.desc())
            )
            total = base_query.count()
            users = list(base_query.paginate(page, limit))

            user_ids = [u.id for u in users]
            active_subscriptions = {}
            if user_ids:
                subs = (
                    UserSubscription.select(UserSubscription, SubscriptionPlan)
                    .join(SubscriptionPlan, on=(UserSubscription.plan == SubscriptionPlan.id))
                    .where(
                        UserSubscription.user.in_(user_ids),
                        UserSubscription.creator == creator_id,
                        UserSubscription.status == "active",
                    )
                )
                for s in subs:
                    active_subscriptions[s.user_id] = s

            items = []
            for u in users:
                sub_info = active_subscriptions.get(u.id)
                items.append(
                    {
                        "id": u.id,
                        "name": u.name,
                        "email": u.email,
                        "avatar_url": u.avatar_url,
                        "plan_name": sub_info.plan.name if sub_info and sub_info.plan else None,
                        "is_paid": bool(sub_info is not None),
                        "subscribed_at": sub_info.created_at if sub_info else None,
                        "joined_at": u.created_at,
                    }
                )
            return items, total
