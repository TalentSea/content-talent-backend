import calendar
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from fastapi import HTTPException, status

from app.config import get_settings
from app.database import db_proxy
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.repositories.mobile.payment_repository import PaymentRepository
from app.repositories.mobile.user_subscription_repository import (
    UserSubscriptionRepository,
)
from app.schemas.mobile.payment_schemas import (
    CreateOrderResponse,
    SubscriptionDTO,
    SubscriptionStatusResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)

logger = logging.getLogger(__name__)


def calculate_end_date(
    start_date: datetime, period_value: int, period_unit: str
) -> datetime:
    """
    Computes accurate expiration datetime taking into account days, weeks, months, and leap years.
    """
    unit = (period_unit or "months").lower()
    if unit == "days":
        return start_date + timedelta(days=period_value)
    elif unit == "weeks":
        return start_date + timedelta(weeks=period_value)
    elif unit == "months":
        year = start_date.year + (start_date.month + period_value - 1) // 12
        month = (start_date.month + period_value - 1) % 12 + 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(start_date.day, max_day)
        return start_date.replace(year=year, month=month, day=day)
    elif unit == "years":
        year = start_date.year + period_value
        max_day = calendar.monthrange(year, start_date.month)[1]
        day = min(start_date.day, max_day)
        return start_date.replace(year=year, month=start_date.month, day=day)
    else:
        return start_date + timedelta(days=period_value * 30)


class MobilePaymentService:
    """
    Business logic orchestration for Razorpay Orders, cryptographic HMAC verification,
    idempotent subscription unlocks, and webhook safety net.
    """

    def __init__(
        self,
        payment_repo: PaymentRepository | None = None,
        subscription_repo: UserSubscriptionRepository | None = None,
    ):
        self.payment_repo = payment_repo or PaymentRepository()
        self.subscription_repo = subscription_repo or UserSubscriptionRepository()

    def _to_subscription_dto(self, sub: UserSubscription) -> SubscriptionDTO:
        now = datetime.now(timezone.utc)
        end_date_aware = (
            sub.end_date
            if sub.end_date.tzinfo
            else sub.end_date.replace(tzinfo=timezone.utc)
        )
        days_remaining = max(0, (end_date_aware.date() - now.date()).days)

        return SubscriptionDTO(
            id=sub.id,
            plan_id=sub.plan_id,
            plan_name=sub.plan.name,
            billing_period_value=sub.plan.billing_period_value,
            billing_period_unit=sub.plan.billing_period_unit,
            status=sub.status,
            start_date=sub.start_date,
            end_date=sub.end_date,
            days_remaining=days_remaining,
        )

    def create_order(
        self, subscriber_context: dict[str, Any], plan_id: int
    ) -> CreateOrderResponse:
        """
        Creates a Razorpay order after verifying that the subscriber does not have an active subscription.
        """
        user_id = subscriber_context.get("user_id")
        creator_id = subscriber_context.get("creator_id")
        settings = get_settings()

        # 1. Active Subscription Guard
        active_sub = self.subscription_repo.get_active_subscription(user_id, creator_id)
        if active_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ACTIVE_SUBSCRIPTION_EXISTS",
            )

        # 2. Fetch Plan Tier
        plan = SubscriptionPlan.get_or_none(
            (SubscriptionPlan.id == plan_id)
            & (SubscriptionPlan.user == creator_id)
            & (SubscriptionPlan.is_active == 1)
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PLAN_NOT_FOUND",
            )

        # 3. Currency Subunit Conversion (₹ INR to Paise)
        final_price = float(plan.final_price)
        amount_paise = round(final_price * 100)
        if amount_paise < 100:
            logger.warning(
                "Plan %s final_price (₹%s = %s paise) is below Razorpay gateway minimum of 100 paise.",
                plan.id,
                final_price,
                amount_paise,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PLAN_AMOUNT_BELOW_GATEWAY_MINIMUM",
            )

        # 4. Generate Official Order via Razorpay REST API
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.error("Razorpay API credentials not configured in environment.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PAYMENT_GATEWAY_NOT_CONFIGURED",
            )

        order_id: str = ""
        try:
            url = "https://api.razorpay.com/v1/orders"
            auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            receipt_str = f"sub_{user_id}_p{plan_id}_{int(datetime.now(timezone.utc).timestamp())}"[
                :40
            ]
            payload = {
                "amount": amount_paise,
                "currency": plan.currency or "INR",
                "receipt": receipt_str,
            }
            res = requests.post(url, json=payload, auth=auth, timeout=10)
            if res.status_code not in (200, 201):
                logger.error(
                    "Razorpay Order API failed (%s): %s", res.status_code, res.text
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="PAYMENT_GATEWAY_ERROR",
                )
            order_id = res.json().get("id", "")
            if not order_id:
                logger.error("Razorpay response missing order ID: %s", res.text)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="PAYMENT_GATEWAY_ERROR",
                )
        except requests.RequestException as req_err:
            logger.error("Failed contacting Razorpay Order API: %s", req_err)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PAYMENT_GATEWAY_UNAVAILABLE",
            )

        # 5. Insert Transaction Record in Database
        payment = self.payment_repo.create_payment(
            user_id=user_id,
            creator_id=creator_id,
            plan_id=plan.id,
            razorpay_order_id=order_id,
            amount=final_price,
            currency=plan.currency or "INR",
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PAYMENT_INITIALIZATION_FAILED",
            )

        return CreateOrderResponse(
            order_id=order_id,
            amount=amount_paise,
            currency=plan.currency or "INR",
            key_id=settings.RAZORPAY_KEY_ID,
        )

    def verify_payment(
        self, subscriber_context: dict[str, Any], payload: VerifyPaymentRequest
    ) -> VerifyPaymentResponse:
        """
        Verifies cryptographic HMAC-SHA256 signature and idempotently activates subscriber access.
        """
        user_id = subscriber_context.get("user_id")
        creator_id = subscriber_context.get("creator_id")
        settings = get_settings()

        payment = self.payment_repo.get_payment_by_order_id(payload.razorpay_order_id)
        if (
            not payment
            or payment.user_id != user_id
            or payment.creator_id != creator_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ORDER_NOT_FOUND",
            )

        # 1. Idempotency Check
        if payment.status == "captured":
            existing_sub = self.subscription_repo.get_subscription_by_payment(
                payment.id
            )
            if existing_sub:
                return VerifyPaymentResponse(
                    status="success",
                    subscription=self._to_subscription_dto(existing_sub),
                )

        # 2. Cryptographic HMAC-SHA256 Signature Verification
        key_secret = settings.RAZORPAY_KEY_SECRET
        data_to_sign = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
        expected_signature = hmac.new(
            key_secret.encode("utf-8"),
            data_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
            logger.warning(
                "Invalid payment signature for order %s: expected %s, got %s",
                payload.razorpay_order_id,
                expected_signature,
                payload.razorpay_signature,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_PAYMENT_SIGNATURE",
            )

        # 3. Atomically Mark Captured, Create Subscription & Increment Counter Cache
        with db_proxy.atomic():
            self.payment_repo.mark_captured(
                order_id=payload.razorpay_order_id,
                razorpay_payment_id=payload.razorpay_payment_id,
                razorpay_signature=payload.razorpay_signature,
            )

            # 4. Calculate Validity Window
            start_date = datetime.now(timezone.utc)
            end_date = calculate_end_date(
                start_date,
                payment.plan.billing_period_value,
                payment.plan.billing_period_unit,
            )

            # 5. Create Active User Subscription Entitlement
            sub = self.subscription_repo.create_subscription(
                user_id=user_id,
                creator_id=creator_id,
                plan_id=payment.plan_id,
                payment_id=payment.id,
                start_date=start_date,
                end_date=end_date,
            )
            if not sub:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUBSCRIPTION_ACTIVATION_FAILED",
                )

            # 6. Increment Plan's Active Subscribers Counter Cache
            SubscriptionPlan.update(
                active_subscribers=SubscriptionPlan.active_subscribers + 1
            ).where(SubscriptionPlan.id == payment.plan_id).execute()

        return VerifyPaymentResponse(
            status="success",
            subscription=self._to_subscription_dto(sub),
        )

    def get_subscription_status(
        self, subscriber_context: dict[str, Any]
    ) -> SubscriptionStatusResponse:
        """
        Retrieves active membership entitlement status for current authenticated subscriber.
        """
        user_id = subscriber_context.get("user_id")
        creator_id = subscriber_context.get("creator_id")

        active_sub = self.subscription_repo.get_active_subscription(user_id, creator_id)
        if not active_sub:
            return SubscriptionStatusResponse(
                has_active_subscription=False,
                subscription=None,
            )

        return SubscriptionStatusResponse(
            has_active_subscription=True,
            subscription=self._to_subscription_dto(active_sub),
        )

    def handle_webhook(self, raw_body: bytes, signature: str | None) -> dict[str, str]:
        """
        Processes asynchronous server-to-server Razorpay webhook events as a fallback safety net.
        """
        settings = get_settings()

        # 1. Verify Webhook Signature on Raw Bytes
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.error("RAZORPAY_WEBHOOK_SECRET is not configured in environment.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="WEBHOOK_VERIFICATION_NOT_CONFIGURED",
            )

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MISSING_WEBHOOK_SIGNATURE",
            )

        expected_sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            logger.warning("Invalid Razorpay webhook signature received.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_WEBHOOK_SIGNATURE",
            )

        # 2. Parse Event Payload
        try:
            event_data = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            logger.error("Malformed webhook JSON payload: %s", err)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MALFORMED_WEBHOOK_PAYLOAD",
            )

        event_name = event_data.get("event")
        payload = event_data.get("payload", {})
        payment_entity = payload.get("payment", {}).get("entity", {})

        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        if not order_id:
            return {"status": "success"}

        payment = self.payment_repo.get_payment_by_order_id(order_id)
        if not payment:
            logger.info("Webhook received for unknown order %s, skipping", order_id)
            return {"status": "success"}

        if event_name == "payment.captured":
            # Idempotent Activation Safety Net
            existing_sub = self.subscription_repo.get_subscription_by_payment(
                payment.id
            )
            if not existing_sub and payment.status != "captured":
                with db_proxy.atomic():
                    self.payment_repo.mark_captured(order_id, payment_id)
                    start_date = datetime.now(timezone.utc)
                    end_date = calculate_end_date(
                        start_date,
                        payment.plan.billing_period_value,
                        payment.plan.billing_period_unit,
                    )
                    self.subscription_repo.create_subscription(
                        user_id=payment.user_id,
                        creator_id=payment.creator_id,
                        plan_id=payment.plan_id,
                        payment_id=payment.id,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    SubscriptionPlan.update(
                        active_subscribers=SubscriptionPlan.active_subscribers + 1
                    ).where(SubscriptionPlan.id == payment.plan_id).execute()
                    logger.info(
                        "Subscription activated via webhook for order %s", order_id
                    )

        elif event_name == "payment.failed":
            error_code = payment_entity.get("error_code")
            error_desc = payment_entity.get("error_description")
            self.payment_repo.mark_failed(
                order_id=order_id,
                razorpay_payment_id=payment_id,
                error_code=error_code,
                error_description=error_desc,
            )
            logger.info(
                "Payment marked failed via webhook for order %s: %s",
                order_id,
                error_desc,
            )

        return {"status": "success"}
