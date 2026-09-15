from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateOrderRequest(BaseModel):
    """
    Request payload to initiate a Razorpay order for a selected subscription plan.
    """

    plan_id: int = Field(
        ..., gt=0, description="Unique ID of subscription plan to purchase"
    )


class CreateOrderResponse(BaseModel):
    """
    Response envelope containing Razorpay SDK initialization parameters.
    """

    order_id: str = Field(
        ..., description="Razorpay official order ID (e.g. order_...)"
    )
    amount: int = Field(..., description="Amount in paise (e.g. 249900)")
    currency: str = Field(default="INR", description="Currency ISO code")
    key_id: str = Field(..., description="Razorpay public API key ID")


class VerifyPaymentRequest(BaseModel):
    """
    Cryptographic verification payload received from Razorpay SDK upon successful payment.
    """

    razorpay_order_id: str = Field(..., description="Razorpay Order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay Payment ID")
    razorpay_signature: str = Field(
        ..., description="Cryptographic HMAC-SHA256 signature string"
    )


class SubscriptionDTO(BaseModel):
    """
    Unified active subscription entitlement DTO shared across verification and status endpoints.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique user subscription ID")
    plan_id: int = Field(..., description="Subscribed plan tier ID")
    plan_name: str = Field(
        ..., description="Name of the subscribed plan (e.g. Premium)"
    )
    billing_period_value: int = Field(
        ..., description="Duration interval quantity (e.g. 24)"
    )
    billing_period_unit: str = Field(
        ..., description="Duration interval unit (e.g. months)"
    )
    status: str = Field(..., description="Entitlement status (active, expired)")
    start_date: datetime = Field(..., description="Access validity start timestamp")
    end_date: datetime = Field(..., description="Access expiration timestamp")
    days_remaining: int = Field(..., description="Days remaining until expiration")


class VerifyPaymentResponse(BaseModel):
    """
    Response envelope for successful payment verification and subscription activation.
    """

    status: str = Field(default="success", description="Outcome status")
    subscription: SubscriptionDTO = Field(
        ..., description="Activated subscription details"
    )


class SubscriptionStatusResponse(BaseModel):
    """
    Current subscriber membership status response.
    """

    has_active_subscription: bool = Field(
        ..., description="Whether user holds an active, unexpired subscription"
    )
    subscription: SubscriptionDTO | None = Field(
        default=None, description="Active subscription details if enrolled"
    )


class RazorpayWebhookEvent(BaseModel):
    """
    Envelope for Razorpay server-to-server webhook callbacks.
    """

    entity: str = Field(default="event", description="Event entity type")
    event: str = Field(
        ..., description="Event name (e.g. payment.captured, payment.failed)"
    )
    contains: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
