from datetime import datetime
from typing import List, Optional, Tuple
from peewee import fn
from app.models.subscriber import Subscriber

class SubscriberRepository:
    """
    Data access layer for subscribers.
    """

    def create_subscriber(self, subscriber_data: dict, user_id: int) -> Subscriber:
        return Subscriber.create(user=user_id, **subscriber_data)

    def get_subscriber_by_id(self, subscriber_id: int, user_id: int) -> Optional[Subscriber]:
        return Subscriber.get_or_none((Subscriber.id == subscriber_id) & (Subscriber.user == user_id))

    def get_all_subscribers(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 20,
        plan: Optional[str] = None,
        status: Optional[str] = None,
        join_date_from: Optional[datetime] = None,
        join_date_to: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Subscriber], int]:
        query = Subscriber.select().where(Subscriber.user == user_id)

        if plan:
            query = query.where(Subscriber.plan == plan)
        if status:
            query = query.where(Subscriber.status == status)
        if join_date_from:
            query = query.where(Subscriber.joined_at >= join_date_from)
        if join_date_to:
            query = query.where(Subscriber.joined_at <= join_date_to)
        if search:
            search_term = f"%{search}%"
            query = query.where((Subscriber.name.contains(search_term)) | (Subscriber.email.contains(search_term)))

        total = query.count()
        subscribers = list(query.order_by(Subscriber.joined_at.desc()).paginate(page, limit))
        return subscribers, total

    def get_recent_subscribers(self, user_id: int, limit: int = 5) -> List[Subscriber]:
        query = Subscriber.select().where(Subscriber.user == user_id).order_by(Subscriber.joined_at.desc()).limit(limit)
        return list(query)

    def count_subscribers(self, user_id: int) -> int:
        return Subscriber.select().where(Subscriber.user == user_id).count()

    def count_joined_since(self, user_id: int, threshold: datetime) -> int:
        return Subscriber.select().where((Subscriber.user == user_id) & (Subscriber.joined_at >= threshold)).count()

    def count_joined_between(self, user_id: int, start: datetime, end: datetime) -> int:
        return Subscriber.select().where((Subscriber.user == user_id) & (Subscriber.joined_at >= start) & (Subscriber.joined_at < end)).count()

    def count_by_status(self, user_id: int, status: str) -> int:
        return Subscriber.select().where((Subscriber.user == user_id) & (Subscriber.status == status)).count()

    def avg_total_revenue(self, user_id: int) -> float:
        row = Subscriber.select(fn.AVG(Subscriber.total_revenue).alias("avg_revenue")).where(Subscriber.user == user_id).first()
        return row.avg_revenue if row and row.avg_revenue is not None else 0.0

    def get_plan_distribution(self, user_id: int) -> List[dict]:
        rows = (
            Subscriber
            .select(Subscriber.plan, fn.COUNT(Subscriber.id).alias("count"))
            .where(Subscriber.user == user_id)
            .group_by(Subscriber.plan)
        )
        total = self.count_subscribers(user_id)
        return [
            {
                "plan": row.plan,
                "count": row.count,
                "percentage": round((row.count / total) * 100, 1) if total else 0.0
            }
            for row in rows
        ]

    def update_subscriber_plan(self, subscriber_id: int, user_id: int, plan: str) -> Optional[Subscriber]:
        subscriber = self.get_subscriber_by_id(subscriber_id, user_id)
        if not subscriber:
            return None
        subscriber.plan = plan
        subscriber.save()
        return subscriber

    def set_subscriber_status(self, subscriber_id: int, user_id: int, status: str) -> Optional[Subscriber]:
        subscriber = self.get_subscriber_by_id(subscriber_id, user_id)
        if not subscriber:
            return None
        subscriber.status = status
        subscriber.last_active_at = subscriber.last_active_at if status == "active" else subscriber.last_active_at
        subscriber.save()
        return subscriber
