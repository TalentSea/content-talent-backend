from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app.repositories.admin.dashboard_repository import DashboardRepository
from app.schemas.admin.dashboard_schemas import (
    AnalyticsDataPoint,
    AnalyticsResponse,
    ContentInventoryBreakdown,
    DashboardStatsResponse,
    GrowthMetric,
    RecentActivityUserItem,
    SubscriptionBreakdownResponse,
    SubscriptionTierItem,
)
from app.schemas.shared.common_schemas import PaginatedResponse

# Standard IST timezone for business metrics
IST = ZoneInfo("Asia/Kolkata")


def compute_growth_percentage(current_val: float | int, previous_val: float | int) -> float:
    """
    Computes period-over-period percentage growth adhering to the division-by-zero
    mathematical model defined in the API specification.
    """
    c = float(current_val)
    p = float(previous_val)

    if p == 0.0 and c > 0.0:
        return 100.0
    if p == 0.0 and c == 0.0:
        return 0.0
    if p > 0.0 and c == 0.0:
        return -100.0
    return round(((c - p) / p) * 100.0, 1)


class DashboardService:
    """
    Business logic layer for Creator Studio Dashboard & Analytics APIs.
    Coordinates date range mathematics, metric normalization, and response aggregation.
    """

    def __init__(self, repo: DashboardRepository | None = None) -> None:
        self.repo = repo or DashboardRepository()

    def _resolve_date_boundaries(
        self,
        range_preset: str | None,
        start_date_str: str | None,
        end_date_str: str | None,
        default_preset: str = "30d",
    ) -> tuple[datetime, datetime, datetime, datetime, date, date]:
        """
        Resolves ISO date boundaries for current and symmetric prior comparison windows.
        Returns (curr_start_dt, curr_end_dt, prev_start_dt, prev_end_dt, start_date, end_date).
        """
        now_ist = datetime.now(IST)

        if start_date_str and end_date_str:
            try:
                start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Expected YYYY-MM-DD.",
                )
            if start_d > end_d:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date cannot be after end_date.",
                )
        else:
            preset = (range_preset or default_preset).lower()
            end_d = now_ist.date()
            if preset == "7d":
                start_d = end_d - timedelta(days=6)
            elif preset == "30d":
                start_d = end_d - timedelta(days=29)
            elif preset == "90d":
                start_d = end_d - timedelta(days=89)
            elif preset in ("6m", "180d"):
                start_d = end_d - timedelta(days=179)
            elif preset in ("12m", "1y", "365d"):
                start_d = end_d - timedelta(days=364)
            else:
                # Default fallback 30d
                start_d = end_d - timedelta(days=29)

        curr_start_dt = datetime(
            start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=IST
        )
        curr_end_dt = datetime(
            end_d.year, end_d.month, end_d.day, 23, 59, 59, 999999, tzinfo=IST
        )

        duration = curr_end_dt - curr_start_dt
        prev_end_dt = curr_start_dt - timedelta(microseconds=1)
        prev_start_dt = curr_start_dt - duration

        return curr_start_dt, curr_end_dt, prev_start_dt, prev_end_dt, start_d, end_d

    def get_dashboard_stats(
        self,
        creator_id: int,
        range_preset: str | None = "30d",
        start_date_str: str | None = None,
        end_date_str: str | None = None,
    ) -> DashboardStatsResponse:
        """
        GET /api/v1/admin/dashboard/stats — High-level summary cards with growth telemetry.
        """
        (
            curr_start,
            curr_end,
            prev_start,
            prev_end,
            start_d,
            end_d,
        ) = self._resolve_date_boundaries(
            range_preset, start_date_str, end_date_str, default_preset="30d"
        )

        # 1. Total Revenue
        rev_curr = self.repo.get_revenue_in_window(creator_id, curr_start, curr_end)
        rev_prev = self.repo.get_revenue_in_window(creator_id, prev_start, prev_end)
        revenue_metric = GrowthMetric(
            current=round(rev_curr, 2),
            previous=round(rev_prev, 2),
            growth_percentage=compute_growth_percentage(rev_curr, rev_prev),
        )

        # 2. Total Views
        views_curr = self.repo.get_views_in_window(creator_id, curr_start, curr_end)
        views_prev = self.repo.get_views_in_window(creator_id, prev_start, prev_end)
        if views_curr == 0 and views_prev == 0:
            # If no time-windowed watch histories exist, surface lifetime video views as baseline
            lifetime = self.repo.get_lifetime_views(creator_id)
            views_curr = lifetime

        views_metric = GrowthMetric(
            current=views_curr,
            previous=views_prev,
            growth_percentage=compute_growth_percentage(views_curr, views_prev),
        )

        # 3. Total Users (Registered accounts)
        users_curr = self.repo.get_total_registered_users(creator_id)
        users_in_win = self.repo.get_user_registrations_in_window(
            creator_id, curr_start, curr_end
        )
        users_prev = max(users_curr - users_in_win, 0)
        users_metric = GrowthMetric(
            current=users_curr,
            previous=users_prev,
            growth_percentage=compute_growth_percentage(users_curr, users_prev),
        )

        # 4. Total Subscribers (Active paying members)
        subs_curr = self.repo.get_active_subscribers_count(creator_id)
        subs_in_win = self.repo.get_subscribers_converted_in_window(
            creator_id, curr_start, curr_end
        )
        subs_prev = max(subs_curr - subs_in_win, 0)
        subs_metric = GrowthMetric(
            current=subs_curr,
            previous=subs_prev,
            growth_percentage=compute_growth_percentage(subs_curr, subs_prev),
        )

        # 5. Catalog Inventory Breakdown
        inventory = self.repo.get_content_inventory(creator_id, curr_start)
        inventory_metric = ContentInventoryBreakdown(**inventory)

        return DashboardStatsResponse(
            start_date=start_d,
            end_date=end_d,
            currency="INR",
            total_revenue=revenue_metric,
            total_views=views_metric,
            total_users=users_metric,
            total_subscribers=subs_metric,
            total_content=inventory_metric,
        )

    def get_analytics(
        self,
        creator_id: int,
        range_preset: str | None = "6m",
        start_date_str: str | None = None,
        end_date_str: str | None = None,
        interval: str | None = None,
    ) -> AnalyticsResponse:
        """
        GET /api/v1/admin/dashboard/analytics — Chronological time-series chart points.
        """
        (
            curr_start,
            curr_end,
            _,
            _,
            start_d,
            end_d,
        ) = self._resolve_date_boundaries(
            range_preset, start_date_str, end_date_str, default_preset="6m"
        )

        duration_days = (end_d - start_d).days + 1

        # Auto-resolve interval if omitted based on spec matrix
        if not interval:
            if duration_days <= 30:
                resolved_interval = "day"
            elif duration_days <= 90:
                resolved_interval = "week"
            else:
                resolved_interval = "month"
        else:
            resolved_interval = interval.lower()
            if resolved_interval not in ("day", "week", "month"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid interval. Supported intervals are: 'day', 'week', 'month'.",
                )

        # Generate chronological bucket time slices
        buckets: list[tuple[datetime, datetime, str, str]] = []
        cursor = curr_start

        if resolved_interval == "day":
            while cursor <= curr_end:
                b_start = cursor
                b_end = datetime(
                    cursor.year, cursor.month, cursor.day, 23, 59, 59, 999999, tzinfo=IST
                )
                date_str = b_start.strftime("%Y-%m-%d")
                label_str = b_start.strftime("%d %b")
                buckets.append((b_start, b_end, date_str, label_str))
                cursor += timedelta(days=1)

        elif resolved_interval == "week":
            while cursor <= curr_end:
                b_start = cursor
                next_week = cursor + timedelta(days=7)
                b_end = min(next_week - timedelta(microseconds=1), curr_end)
                date_str = b_start.strftime("%Y-%m-%d")
                label_str = f"{b_start.strftime('%d %b')}"
                buckets.append((b_start, b_end, date_str, label_str))
                cursor = next_week

        else:  # "month"
            while cursor <= curr_end:
                b_start = cursor
                # Advance to next month
                if cursor.month == 12:
                    next_month = datetime(cursor.year + 1, 1, 1, tzinfo=IST)
                else:
                    next_month = datetime(cursor.year, cursor.month + 1, 1, tzinfo=IST)
                b_end = min(next_month - timedelta(microseconds=1), curr_end)
                date_str = b_start.strftime("%Y-%m-%d")
                label_str = b_start.strftime("%b")
                buckets.append((b_start, b_end, date_str, label_str))
                cursor = next_month

        data_points: list[AnalyticsDataPoint] = []
        for b_start, b_end, d_str, l_str in buckets:
            u_count = self.repo.get_user_registrations_in_window(
                creator_id, b_start, b_end
            )
            s_count = self.repo.get_subscribers_converted_in_window(
                creator_id, b_start, b_end
            )
            rev_val = self.repo.get_revenue_in_window(creator_id, b_start, b_end)
            v_count = self.repo.get_views_in_window(creator_id, b_start, b_end)

            data_points.append(
                AnalyticsDataPoint(
                    date=d_str,
                    label=l_str,
                    users=u_count,
                    subscribers=s_count,
                    revenue=round(rev_val, 2),
                    views=v_count,
                )
            )

        return AnalyticsResponse(
            start_date=start_d.isoformat(),
            end_date=end_d.isoformat(),
            interval=resolved_interval,
            currency="INR",
            data_points=data_points,
        )

    def get_subscription_breakdown(
        self,
        creator_id: int,
        range_preset: str | None = "30d",
        start_date_str: str | None = None,
        end_date_str: str | None = None,
    ) -> SubscriptionBreakdownResponse:
        """
        GET /api/v1/admin/dashboard/subscription-breakdown — Subscriber distribution and period revenue per tier.
        """
        (
            curr_start,
            curr_end,
            _,
            _,
            start_d,
            end_d,
        ) = self._resolve_date_boundaries(
            range_preset, start_date_str, end_date_str, default_preset="30d"
        )

        raw_tiers = self.repo.get_subscription_tier_breakdown(
            creator_id, curr_start, curr_end
        )

        total_subscribers = sum(t["subscribers"] for t in raw_tiers)
        total_revenue = round(sum(t["revenue"] for t in raw_tiers), 2)

        tier_items: list[SubscriptionTierItem] = []
        for t in raw_tiers:
            subs_cnt = t["subscribers"]
            subs_pct = (
                round((subs_cnt / total_subscribers) * 100.0, 1)
                if total_subscribers > 0
                else 0.0
            )
            rev_val = t["revenue"]
            rev_pct = (
                round((rev_val / total_revenue) * 100.0, 1)
                if total_revenue > 0.0
                else 0.0
            )
            tier_items.append(
                SubscriptionTierItem(
                    plan_id=t["plan_id"],
                    name=t["name"],
                    badge_text=t["badge_text"],
                    is_active=t["is_active"],
                    subscribers=subs_cnt,
                    subscribers_percentage=subs_pct,
                    revenue=rev_val,
                    revenue_percentage=rev_pct,
                )
            )

        return SubscriptionBreakdownResponse(
            start_date=start_d,
            end_date=end_d,
            currency="INR",
            total_subscribers=total_subscribers,
            total_revenue=total_revenue,
            tiers=tier_items,
        )

    def get_recent_activity(
        self,
        creator_id: int,
        filter_type: str = "all",
        page: int = 1,
        limit: int = 5,
    ) -> PaginatedResponse[RecentActivityUserItem]:
        """
        GET /api/v1/admin/dashboard/recent-activity — Paginated members feed.
        """
        normalized_filter = (filter_type or "all").lower()
        if normalized_filter not in ("all", "subscribers", "users"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filter. Supported filters are: 'all', 'subscribers', 'users'.",
            )

        page_val = max(int(page), 1)
        limit_val = min(max(int(limit), 1), 20)

        raw_items, total = self.repo.get_recent_activity(
            creator_id=creator_id,
            filter_type=normalized_filter,
            page=page_val,
            limit=limit_val,
        )

        items = [RecentActivityUserItem(**item) for item in raw_items]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page_val,
            limit=limit_val,
        )
