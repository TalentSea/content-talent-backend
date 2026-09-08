import logging
from datetime import datetime, timezone

from peewee import PeeweeException

from app.models.payment import Payment
from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


class PaymentRepository:
    """
    Data access layer for payment records and gateway transaction state tracking.
    """

    def create_payment(
        self,
        user_id: int,
        creator_id: int,
        plan_id: int,
        razorpay_order_id: str,
        amount: float,
        currency: str = "INR",
    ) -> Payment | None:
        """
        Creates a new payment record initialized in 'created' status.
        """
        try:
            return Payment.create(
                user=user_id,
                creator=creator_id,
                plan=plan_id,
                razorpay_order_id=razorpay_order_id,
                amount=amount,
                currency=currency,
                status="created",
            )
        except PeeweeException as err:
            logger.error("Error creating payment order %s: %s", razorpay_order_id, err)
            return None

    def get_payment_by_order_id(self, order_id: str) -> Payment | None:
        """
        Retrieves a payment record by its unique Razorpay Order ID, eager loading SubscriptionPlan.
        """
        try:
            return (
                Payment.select(Payment, SubscriptionPlan)
                .join(SubscriptionPlan)
                .where(Payment.razorpay_order_id == order_id)
                .first()
            )
        except PeeweeException as err:
            logger.error("Error fetching payment by order_id %s: %s", order_id, err)
            return None

    def get_payment_by_payment_id(self, payment_id: str) -> Payment | None:
        """
        Retrieves a payment record by its unique Razorpay Payment ID, eager loading SubscriptionPlan.
        """
        try:
            return (
                Payment.select(Payment, SubscriptionPlan)
                .join(SubscriptionPlan)
                .where(Payment.razorpay_payment_id == payment_id)
                .first()
            )
        except PeeweeException as err:
            logger.error("Error fetching payment by payment_id %s: %s", payment_id, err)
            return None

    def mark_captured(
        self,
        order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str | None = None,
    ) -> Payment | None:
        """
        Updates payment status to 'captured' and records payment ID and signature.
        """
        try:
            payment = Payment.get_or_none(Payment.razorpay_order_id == order_id)
            if not payment:
                return None

            payment.status = "captured"
            payment.razorpay_payment_id = razorpay_payment_id
            if razorpay_signature:
                payment.razorpay_signature = razorpay_signature
            payment.updated_at = datetime.now(timezone.utc)
            payment.save()
            return payment
        except PeeweeException as err:
            logger.error("Error marking payment %s as captured: %s", order_id, err)
            return None

    def mark_failed(
        self,
        order_id: str,
        razorpay_payment_id: str | None = None,
        error_code: str | None = None,
        error_description: str | None = None,
    ) -> Payment | None:
        """
        Updates payment status to 'failed' and logs gateway decline reason.
        """
        try:
            payment = Payment.get_or_none(Payment.razorpay_order_id == order_id)
            if not payment:
                return None

            payment.status = "failed"
            if razorpay_payment_id:
                payment.razorpay_payment_id = razorpay_payment_id
            payment.error_code = error_code
            payment.error_description = error_description
            payment.updated_at = datetime.now(timezone.utc)
            payment.save()
            return payment
        except PeeweeException as err:
            logger.error("Error marking payment %s as failed: %s", order_id, err)
            return None
