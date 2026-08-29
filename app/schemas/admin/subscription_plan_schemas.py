from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SubscriptionPlanCreateRequest(BaseModel):
    """
    Request payload for creating a new subscription plan tier.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Plan title")
    base_price: float = Field(..., ge=0.0, description="Base non-discounted price in ₹")
    discount_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Discount percentage (0 to 100)"
    )
    billing_period_value: int = Field(
        default=1, ge=1, le=365, description="Billing period interval quantity"
    )
    billing_period_unit: str = Field(
        default="months",
        description="Billing period unit: 'days', 'months', or 'years'",
    )
    description: str | None = Field(
        default=None, max_length=500, description="Short tagline or summary"
    )
    features: list[str] = Field(
        default_factory=list, description="Array of benefit strings for card checklist"
    )
    badge_text: str | None = Field(
        default=None, max_length=50, description="Marketing highlight tag (e.g. '15% OFF', '⚡')"
    )
    is_active: bool = Field(
        default=True, description="Whether the plan is visible to subscribers"
    )


class SubscriptionPlanUpdateRequest(BaseModel):
    """
    Request payload for updating an existing subscription plan tier.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    base_price: float | None = Field(default=None, ge=0.0)
    discount_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    billing_period_value: int | None = Field(default=None, ge=1, le=365)
    billing_period_unit: str | None = Field(default=None)
    description: str | None = Field(default=None, max_length=500)
    features: list[str] | None = Field(default=None)
    badge_text: str | None = Field(default=None, max_length=50)
    is_active: bool | None = Field(default=None)


class SubscriptionPlanReorderRequest(BaseModel):
    """
    Request payload for batch reordering subscription plan display sequence.
    """

    ids: list[int] = Field(
        ..., min_length=1, description="List of plan IDs in the desired display order"
    )


class SubscriptionPlanItemResponse(BaseModel):
    """
    Response DTO representing a creator subscription plan with live stats.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    base_price: float
    discount_percentage: float = 0.0
    final_price: float
    currency: str = "INR"
    billing_period_value: int = 1
    billing_period_unit: str = "months"
    features: list[str] = Field(default_factory=list)
    badge_text: str | None = None
    is_active: bool = True
    display_order: int = 1
    active_subscribers: int = 0
    monthly_revenue: float = 0.0
    created_at: datetime
    updated_at: datetime


class SubscriptionPlanToggleActiveResponse(BaseModel):
    """
    Response DTO for quick active status toggle.
    """

    id: int
    name: str
    is_active: bool
    updated_at: datetime
