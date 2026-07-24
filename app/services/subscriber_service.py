from datetime import datetime, timedelta
from typing import List
from fastapi import HTTPException, status
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.subscriber_schemas import (
    SubscriberItemResponse,
    SubscriberProfileResponse,
    SubscriberStatsResponse,
    PlanDistributionItem,
    UpdateSubscriberPlanRequest,
    EmailSubscriberRequest,
    SuspendSubscriberRequest
)
from app.schemas.common_schemas import PaginatedResponse

class SubscriberService:
    """
    Business logic for subscriber management.
    """

    def __init__(self):
        self.repo = SubscriberRepository()

    def _to_item_response(self, subscriber) -> SubscriberItemResponse:
        return SubscriberItemResponse(
            id=subscriber.id,
            name=subscriber.name,
            email=subscriber.email,
            plan=subscriber.plan,
            status=subscriber.status,
            revenue=subscriber.revenue,
            joined_at=subscriber.joined_at,
            avatar=subscriber.avatar,
        )

    def _to_profile_response(self, subscriber) -> SubscriberProfileResponse:
        return SubscriberProfileResponse(
            id=subscriber.id,
            name=subscriber.name,
            email=subscriber.email,
            plan=subscriber.plan,
            status=subscriber.status,
            total_revenue=subscriber.total_revenue,
            revenue=subscriber.revenue,
            joined_at=subscriber.joined_at,
            last_active_at=subscriber.last_active_at,
            avatar=subscriber.avatar,
        )

    def get_stats(self, user_id: int) -> SubscriberStatsResponse:
        now = datetime.utcnow()
        total = self.repo.count_subscribers(user_id)
        recent_since = now - timedelta(days=30)
        previous_since = now - timedelta(days=60)

        recent_count = self.repo.count_joined_since(user_id, recent_since)
        prev_count = self.repo.count_joined_between(user_id, previous_since, recent_since)

        growth_rate = 0.0
        if prev_count:
            growth_rate = round(((recent_count - prev_count) / prev_count) * 100, 1)

        churn_rate = 0.0
        if total:
            suspended = self.repo.count_by_status(user_id, "suspended")
            churn_rate = round((suspended / total) * 100, 1)

        avg_revenue = round(self.repo.avg_total_revenue(user_id), 2)

        return SubscriberStatsResponse(
            total_subscribers=total,
            growth_rate=growth_rate,
            avg_revenue_per_user=avg_revenue,
            churn_rate=churn_rate,
        )

    def get_plan_distribution(self, user_id: int) -> List[PlanDistributionItem]:
        rows = self.repo.get_plan_distribution(user_id)
        return [PlanDistributionItem(**row) for row in rows]

    def list_subscribers(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 20,
        plan: str = None,
        status: str = None,
        join_date_from: datetime = None,
        join_date_to: datetime = None,
        search: str = None,
    ) -> PaginatedResponse[SubscriberItemResponse]:
        subscribers, total = self.repo.get_all_subscribers(
            user_id,
            page=page,
            limit=limit,
            plan=plan,
            status=status,
            join_date_from=join_date_from,
            join_date_to=join_date_to,
            search=search,
        )
        items = [self._to_item_response(sub) for sub in subscribers]
        total_pages = max(1, (total + limit - 1) // limit)
        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items,
        )

    def get_recent_subscribers(self, user_id: int, limit: int = 5) -> List[SubscriberItemResponse]:
        subscribers = self.repo.get_recent_subscribers(user_id, limit)
        return [self._to_item_response(sub) for sub in subscribers]

    def get_subscriber(self, user_id: int, subscriber_id: int) -> SubscriberProfileResponse:
        subscriber = self.repo.get_subscriber_by_id(subscriber_id, user_id)
        if not subscriber:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscriber {subscriber_id} not found")
        return self._to_profile_response(subscriber)

    def change_plan(self, user_id: int, subscriber_id: int, payload: UpdateSubscriberPlanRequest) -> SubscriberProfileResponse:
        subscriber = self.repo.update_subscriber_plan(subscriber_id, user_id, payload.plan)
        if not subscriber:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscriber {subscriber_id} not found")
        return self._to_profile_response(subscriber)

    def send_email(self, user_id: int, subscriber_id: int, payload: EmailSubscriberRequest) -> dict:
        subscriber = self.repo.get_subscriber_by_id(subscriber_id, user_id)
        if not subscriber:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscriber {subscriber_id} not found")
        # Placeholder for actual email integration
        return {"message": "Email sent successfully"}

    def suspend_subscriber(self, user_id: int, subscriber_id: int, payload: SuspendSubscriberRequest) -> SubscriberProfileResponse:
        subscriber = self.repo.set_subscriber_status(subscriber_id, user_id, "suspended")
        if not subscriber:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscriber {subscriber_id} not found")
        return self._to_profile_response(subscriber)

    def reinstate_subscriber(self, user_id: int, subscriber_id: int) -> SubscriberProfileResponse:
        subscriber = self.repo.set_subscriber_status(subscriber_id, user_id, "active")
        if not subscriber:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscriber {subscriber_id} not found")
        return self._to_profile_response(subscriber)
