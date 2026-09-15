from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionPlanUpdateRequest(BaseModel):
    """
    Request payload for updating an existing subscription plan tier.
    Features, billing interval (1 month), active status, and tier identities are platform-governed.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    base_price: float | None = Field(default=None, ge=0.0)
    discount_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    badge_text: str | None = Field(default=None, max_length=50)


class SubscriptionPlanItemResponse(BaseModel):
    """
    Response DTO representing a creator subscription plan with live stats and built-in features.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_type: str = "with_ads"
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
    display_order: int = 1
    active_subscribers: int = 0
    monthly_revenue: float = 0.0
    created_at: datetime
    updated_at: datetime
