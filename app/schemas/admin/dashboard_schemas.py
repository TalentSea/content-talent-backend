from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# API 1: /stats Schemas
# ---------------------------------------------------------------------------


class GrowthMetric(BaseModel):
    """Encapsulates current value, prior equivalent period value, and growth percentage."""

    current: float | int = Field(..., description="Value in current period")
    previous: float | int = Field(..., description="Value in immediately preceding equivalent period")
    growth_percentage: float = Field(..., description="Period-over-period percentage delta (-100.0% to +100.0%+)")


class ContentInventoryBreakdown(BaseModel):
    """Detailed inventory counts for creator content catalog."""

    total: int = Field(..., description="Lifetime video count")
    published: int = Field(..., description="Playable public videos")
    drafts: int = Field(..., description="Videos in draft, pending or encoding state")
    recently_added: int = Field(..., description="New videos published/uploaded within current date window")


class DashboardStatsResponse(BaseModel):
    """Response DTO for GET /api/v1/admin/dashboard/stats."""

    start_date: date = Field(..., description="Resolved ISO start date of current window")
    end_date: date = Field(..., description="Resolved ISO end date of current window")
    currency: str = Field("INR", description="Three-letter currency code")
    total_revenue: GrowthMetric = Field(..., description="Revenue telemetry and growth")
    total_views: GrowthMetric = Field(..., description="Playback views telemetry and growth")
    total_users: GrowthMetric = Field(..., description="Registered audience accounts telemetry and growth")
    total_subscribers: GrowthMetric = Field(..., description="Active paying subscribers telemetry and growth")
    total_content: ContentInventoryBreakdown = Field(..., description="Creator content catalog inventory breakdown")


# ---------------------------------------------------------------------------
# API 2: /analytics Schemas
# ---------------------------------------------------------------------------


class AnalyticsDataPoint(BaseModel):
    """Chronological time-series point bucketed by day, week, or month."""

    date: str = Field(..., description="ISO boundary date (YYYY-MM-DD) for tooltips & machine sorting")
    label: str = Field(..., description="Human-readable chart label (e.g. '09 Sep', 'Week 36', 'Jun')")
    users: int = Field(..., description="New registered user signups within this interval")
    subscribers: int = Field(..., description="Active paying subscribers count as of this interval")
    revenue: float = Field(..., description="Total captured revenue in ₹ INR within this interval")
    views: int = Field(..., description="Video plays accumulated within this interval")


class AnalyticsResponse(BaseModel):
    """Response DTO for GET /api/v1/admin/dashboard/analytics."""

    start_date: str = Field(..., description="Resolved ISO start date")
    end_date: str = Field(..., description="Resolved ISO end date")
    interval: str = Field(..., description="Bucket interval applied: 'day', 'week', or 'month'")
    currency: str = Field("INR", description="Three-letter currency code")
    data_points: list[AnalyticsDataPoint] = Field(..., description="Ordered chronological array of time points")


# ---------------------------------------------------------------------------
# API 3: /subscription-breakdown Schemas
# ---------------------------------------------------------------------------


class SubscriptionTierItem(BaseModel):
    """Subscription plan tier distribution segment with period revenue and subscriber share."""

    plan_id: int = Field(..., description="Database ID of the subscription plan")
    name: str = Field(..., description="Configured name of the plan")
    badge_text: str | None = Field(None, description="Creator marketing badge text or null")
    is_active: bool = Field(..., description="True if plan is currently active for new purchases, false if retired")
    subscribers: int = Field(..., description="Active enrolled subscribers in this tier")
    subscribers_percentage: float = Field(..., description="Percentage of total subscribers rounded to 1 decimal place")
    revenue: float = Field(..., description="Actual captured revenue in ₹ INR during the selected period")
    revenue_percentage: float = Field(..., description="Percentage of total period revenue rounded to 1 decimal place")


class SubscriptionBreakdownResponse(BaseModel):
    """Response DTO for GET /api/v1/admin/dashboard/subscription-breakdown."""

    start_date: date = Field(..., description="Resolved ISO start date of current window")
    end_date: date = Field(..., description="Resolved ISO end date of current window")
    currency: str = Field("INR", description="Three-letter currency code")
    total_subscribers: int = Field(..., description="Total count of active subscribers across all tiers")
    total_revenue: float = Field(..., description="Total captured revenue in ₹ INR across all tiers in period")
    tiers: list[SubscriptionTierItem] = Field(..., description="Breakdown per subscription plan tier")


# ---------------------------------------------------------------------------
# API 4: /recent-activity Schemas
# ---------------------------------------------------------------------------


class RecentActivityUserItem(BaseModel):
    """Individual member record in the recent activity feed."""

    id: int = Field(..., description="Subscriber account ID")
    name: str | None = Field(None, description="Display name of the user")
    email: str | None = Field(None, description="Email address or null for phone-based/guest registrations")
    avatar_url: str | None = Field(None, description="CDN profile photo URL or null")
    plan_name: str | None = Field(None, description="Name of active subscription plan or null if non-paying")
    is_paid: bool = Field(..., description="True if user currently holds an active paid membership")
    subscribed_at: datetime | None = Field(None, description="ISO timestamp when user subscribed, or null")
    joined_at: datetime = Field(..., description="ISO timestamp when account was registered")
