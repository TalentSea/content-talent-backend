from fastapi import APIRouter, Query, status

from app.dependencies import CurrentAdmin
from app.schemas.admin.dashboard_schemas import (
    AnalyticsResponse,
    DashboardStatsResponse,
    RecentActivityUserItem,
    SubscriptionBreakdownResponse,
)
from app.schemas.shared.common_schemas import PaginatedResponse
from app.services.admin.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Admin Dashboard & Analytics"])
dashboard_service = DashboardService()


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="KPI Overview Cards",
    description="Retrieves summary cards with period-over-period growth telemetry (Revenue, Views, Users, Subscribers, Content Inventory).",
)
def get_dashboard_stats(
    current_user: CurrentAdmin,
    range: str | None = Query(
        "30d", description="Quick preset window: '7d', '30d', '90d', '12m'"
    ),
    start_date: str | None = Query(
        None, description="Custom start date (format: YYYY-MM-DD)"
    ),
    end_date: str | None = Query(
        None, description="Custom end date (format: YYYY-MM-DD)"
    ),
):
    """
    GET /api/v1/admin/dashboard/stats — High-level summary cards.
    """
    return dashboard_service.get_dashboard_stats(
        creator_id=current_user["user_id"],
        range_preset=range,
        start_date_str=start_date,
        end_date_str=end_date,
    )


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Visual Time-Series Analytics Chart",
    description="Returns chronological date-bucketed data points (users, subscribers, revenue, views) for visual area/bar charts.",
)
def get_analytics(
    current_user: CurrentAdmin,
    range: str | None = Query(
        "6m", description="Quick preset window: '7d', '30d', '90d', '6m', '12m'"
    ),
    start_date: str | None = Query(
        None, description="Custom start date (format: YYYY-MM-DD)"
    ),
    end_date: str | None = Query(
        None, description="Custom end date (format: YYYY-MM-DD)"
    ),
    interval: str | None = Query(
        None, description="Date grouping frequency: 'day', 'week', 'month' (auto-selected if omitted)"
    ),
):
    """
    GET /api/v1/admin/dashboard/analytics — Grouped time-series graph points.
    """
    return dashboard_service.get_analytics(
        creator_id=current_user["user_id"],
        range_preset=range,
        start_date_str=start_date,
        end_date_str=end_date,
        interval=interval,
    )


@router.get(
    "/subscription-breakdown",
    response_model=SubscriptionBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Subscription Tier Donut / Pie Chart",
    description="Returns active subscriber distribution and actual captured revenue grouped by plan tier for the selected date window.",
)
def get_subscription_breakdown(
    current_user: CurrentAdmin,
    range: str | None = Query(
        "30d", description="Quick preset window: '7d', '30d', '90d', '12m'"
    ),
    start_date: str | None = Query(
        None, description="Custom start date (format: YYYY-MM-DD)"
    ),
    end_date: str | None = Query(
        None, description="Custom end date (format: YYYY-MM-DD)"
    ),
):
    """
    GET /api/v1/admin/dashboard/subscription-breakdown — Subscriber distribution and period revenue per tier.
    """
    return dashboard_service.get_subscription_breakdown(
        creator_id=current_user["user_id"],
        range_preset=range,
        start_date_str=start_date,
        end_date_str=end_date,
    )


@router.get(
    "/recent-activity",
    response_model=PaginatedResponse[RecentActivityUserItem],
    status_code=status.HTTP_200_OK,
    summary="Recent Mobile Users & Subscribers Feed",
    description="Returns paginated list of recent member signups and paying subscriber conversions, with segmented filtering.",
)
def get_recent_activity(
    current_user: CurrentAdmin,
    filter: str | None = Query(
        "all", description="Classification filter: 'all', 'subscribers', 'users'"
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(5, ge=1, le=20, description="Items per page"),
):
    """
    GET /api/v1/admin/dashboard/recent-activity — Paginated recent members feed.
    """
    return dashboard_service.get_recent_activity(
        creator_id=current_user["user_id"],
        filter_type=filter or "all",
        page=page,
        limit=limit,
    )
