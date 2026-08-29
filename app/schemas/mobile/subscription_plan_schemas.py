from pydantic import BaseModel, ConfigDict, Field


class MobileSubscriptionPlanResponse(BaseModel):
    """
    Response DTO representing an active subscription plan on the mobile checkout paywall.
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
    display_order: int = 1
