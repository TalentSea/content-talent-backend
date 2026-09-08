from fastapi import APIRouter, status

from app.dependencies import CurrentSubscriber
from app.schemas.mobile.payment_schemas import (
    CreateOrderRequest,
    CreateOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.services.mobile.payment_service import MobilePaymentService

router = APIRouter(prefix="/api/v1/mobile/payments", tags=["Mobile Payments"])
payment_service = MobilePaymentService()


@router.post(
    "/create-order",
    response_model=CreateOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialize Razorpay Order",
    description="Initializes a Razorpay order for a selected plan after checking for active subscriptions.",
)
def create_order(payload: CreateOrderRequest, current_subscriber: CurrentSubscriber):
    return payment_service.create_order(
        subscriber_context=current_subscriber,
        plan_id=payload.plan_id,
    )


@router.post(
    "/verify",
    response_model=VerifyPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Payment & Activate Access",
    description="Cryptographically verifies payment HMAC signature and idempotently activates subscription entitlements.",
)
def verify_payment(
    payload: VerifyPaymentRequest, current_subscriber: CurrentSubscriber
):
    return payment_service.verify_payment(
        subscriber_context=current_subscriber,
        payload=payload,
    )
