from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.config import get_settings
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
from app.utils.date_utils import get_app_timezone


def compute_growth_percentage(current_val: float, previous_val: float) -> float:
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
        tz = get_app_timezone()
        now_local = datetime.now(tz)

        if start_date_str and end_date_str:
            try:
                start_d = date.fromisoformat(start_date_str)
                end_d = date.fromisoformat(end_date_str)
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
            end_d = now_local.date()
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
            start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=tz
        )
        curr_end_dt = datetime(
            end_d.year, end_d.month, end_d.day, 23, 59, 59, 999999, tzinfo=tz
        )

        duration = curr_end_dt - curr_start_dt
        prev_end_dt = curr_start_dt - timedelta(microseconds=1)
        prev_start_dt = curr_start_dt - duration

        # Convert to UTC for exact database timestamp queries
        curr_start_utc = curr_start_dt.astimezone(timezone.utc)
        curr_end_utc = curr_end_dt.astimezone(timezone.utc)
        prev_start_utc = prev_start_dt.astimezone(timezone.utc)
        prev_end_utc = prev_end_dt.astimezone(timezone.utc)

        return (
            curr_start_utc,
            curr_end_utc,
            prev_start_utc,
            prev_end_utc,
            start_d,
            end_d,
        )

    def get_dashboard_stats(
        self,
        tenant_id: int,
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
        rev_curr = self.repo.get_revenue_in_window(tenant_id, curr_start, curr_end)
        rev_prev = self.repo.get_revenue_in_window(tenant_id, prev_start, prev_end)
        revenue_metric = GrowthMetric(
            current=round(rev_curr, 2),
            previous=round(rev_prev, 2),
            growth_percentage=compute_growth_percentage(rev_curr, rev_prev),
        )

        # 2. Total Views
        views_curr = self.repo.get_views_in_window(tenant_id, curr_start, curr_end)
        views_prev = self.repo.get_views_in_window(tenant_id, prev_start, prev_end)
        views_metric = GrowthMetric(
            current=views_curr,
            previous=views_prev,
            growth_percentage=compute_growth_percentage(views_curr, views_prev),
        )

        # 3. Total Users (Registered accounts)
        users_curr = self.repo.get_total_registered_users(tenant_id)
        users_in_win = self.repo.get_user_registrations_in_window(
            tenant_id, curr_start, curr_end
        )
        users_prev = max(users_curr - users_in_win, 0)
        users_metric = GrowthMetric(
            current=users_curr,
            previous=users_prev,
            growth_percentage=compute_growth_percentage(users_curr, users_prev),
        )

        # 4. Total Subscribers (Active paying members)
        subs_curr = self.repo.get_active_subscribers_count(tenant_id)
        subs_in_win = self.repo.get_subscribers_converted_in_window(
            tenant_id, curr_start, curr_end
        )
        subs_prev = max(subs_curr - subs_in_win, 0)
        subs_metric = GrowthMetric(
            current=subs_curr,
            previous=subs_prev,
            growth_percentage=compute_growth_percentage(subs_curr, subs_prev),
        )

        # 5. Catalog Inventory Breakdown
        inventory = self.repo.get_content_inventory(tenant_id, curr_start)
        inventory_metric = ContentInventoryBreakdown(**inventory)

        return DashboardStatsResponse(
            start_date=start_d,
            end_date=end_d,
            currency=get_settings().DEFAULT_CURRENCY,
            total_revenue=revenue_metric,
            total_views=views_metric,
            total_users=users_metric,
            total_subscribers=subs_metric,
            total_content=inventory_metric,
        )

    def get_analytics(
        self,
        tenant_id: int,
        range_preset: str | None = "6m",
        start_date_str: str | None = None,
        end_date_str: str | None = None,
        interval: str | None = None,
    ) -> AnalyticsResponse:
        """
        GET /api/v1/admin/dashboard/analytics — Chronological time-series chart points.
        """
        *_, start_d, end_d = self._resolve_date_boundaries(
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

        # Generate chronological bucket time slices using local dates and UTC query bounds
        tz = get_app_timezone()
        buckets: list[tuple[datetime, datetime, str, str]] = []
        cursor_d = start_d

        if resolved_interval == "day":
            while cursor_d <= end_d:
                b_start_local = datetime(
                    cursor_d.year, cursor_d.month, cursor_d.day, 0, 0, 0, tzinfo=tz
                )
                b_end_local = datetime(
                    cursor_d.year,
                    cursor_d.month,
                    cursor_d.day,
                    23,
                    59,
                    59,
                    999999,
                    tzinfo=tz,
                )
                date_str = cursor_d.strftime("%Y-%m-%d")
                label_str = cursor_d.strftime("%d %b")
                buckets.append(
                    (
                        b_start_local.astimezone(timezone.utc),
                        b_end_local.astimezone(timezone.utc),
                        date_str,
                        label_str,
                    )
                )
                cursor_d += timedelta(days=1)

        elif resolved_interval == "week":
            while cursor_d <= end_d:
                next_week_d = min(cursor_d + timedelta(days=6), end_d)
                b_start_local = datetime(
                    cursor_d.year, cursor_d.month, cursor_d.day, 0, 0, 0, tzinfo=tz
                )
                b_end_local = datetime(
                    next_week_d.year,
                    next_week_d.month,
                    next_week_d.day,
                    23,
                    59,
                    59,
                    999999,
                    tzinfo=tz,
                )
                date_str = cursor_d.strftime("%Y-%m-%d")
                label_str = f"{cursor_d.strftime('%d %b')}"
                buckets.append(
                    (
                        b_start_local.astimezone(timezone.utc),
                        b_end_local.astimezone(timezone.utc),
                        date_str,
                        label_str,
                    )
                )
                cursor_d = next_week_d + timedelta(days=1)

        else:  # "month"
            while cursor_d <= end_d:
                if cursor_d.month == 12:
                    month_end_d = date(cursor_d.year, 12, 31)
                    next_month_start_d = date(cursor_d.year + 1, 1, 1)
                else:
                    month_end_d = date(
                        cursor_d.year, cursor_d.month + 1, 1
                    ) - timedelta(days=1)
                    next_month_start_d = date(cursor_d.year, cursor_d.month + 1, 1)
                bucket_end_d = min(month_end_d, end_d)

                b_start_local = datetime(
                    cursor_d.year, cursor_d.month, cursor_d.day, 0, 0, 0, tzinfo=tz
                )
                b_end_local = datetime(
                    bucket_end_d.year,
                    bucket_end_d.month,
                    bucket_end_d.day,
                    23,
                    59,
                    59,
                    999999,
                    tzinfo=tz,
                )
                date_str = cursor_d.strftime("%Y-%m-%d")
                label_str = cursor_d.strftime("%b")
                buckets.append(
                    (
                        b_start_local.astimezone(timezone.utc),
                        b_end_local.astimezone(timezone.utc),
                        date_str,
                        label_str,
                    )
                )
                cursor_d = next_month_start_d

        data_points: list[AnalyticsDataPoint] = []
        for b_start, b_end, d_str, l_str in buckets:
            u_count = self.repo.get_user_registrations_in_window(
                tenant_id, b_start, b_end
            )
            s_count = self.repo.get_subscribers_converted_in_window(
                tenant_id, b_start, b_end
            )
            rev_val = self.repo.get_revenue_in_window(tenant_id, b_start, b_end)
            v_count = self.repo.get_views_in_window(tenant_id, b_start, b_end)

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
            currency=get_settings().DEFAULT_CURRENCY,
            data_points=data_points,
        )

    def get_subscription_breakdown(
        self,
        tenant_id: int,
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
            tenant_id, curr_start, curr_end
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
                    subscribers=subs_cnt,
                    subscribers_percentage=subs_pct,
                    revenue=rev_val,
                    revenue_percentage=rev_pct,
                )
            )

        return SubscriptionBreakdownResponse(
            start_date=start_d,
            end_date=end_d,
            currency=get_settings().DEFAULT_CURRENCY,
            total_subscribers=total_subscribers,
            total_revenue=total_revenue,
            tiers=tier_items,
        )

    def get_recent_activity(
        self,
        tenant_id: int,
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
            tenant_id=tenant_id,
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
