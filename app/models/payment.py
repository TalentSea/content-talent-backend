from datetime import datetime, timezone

from peewee import (
    CharField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    TextField,
)

from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.subscriber import Subscriber
from app.models.subscription_plan import SubscriptionPlan


class Payment(BaseModel):
    """
    Stores financial transaction records and gateway audit trails
    for Razorpay order creation, payment capture, and decline events.
    """

    user = ForeignKeyField(
        model=Subscriber,
        field=Subscriber.id,
        column_name="user_id",
        backref="payments",
        on_delete="CASCADE",
    )
    creator = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="creator_id",
        backref="creator_payments",
        on_delete="CASCADE",
    )
    plan = ForeignKeyField(
        model=SubscriptionPlan,
        field=SubscriptionPlan.id,
        column_name="plan_id",
        backref="plan_payments",
        on_delete="RESTRICT",
    )
    razorpay_order_id = CharField(max_length=100, index=True, null=False)
    razorpay_payment_id = CharField(max_length=100, null=True, index=True)
    razorpay_signature = CharField(max_length=255, null=True)
    amount = FloatField(null=False)
    currency = CharField(max_length=10, default="INR", null=False)
    status = CharField(max_length=30, default="created", index=True, null=False)
    error_code = CharField(max_length=100, null=True)
    error_description = TextField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "payments"
        indexes = (
            (("creator", "status"), False),
            (("user", "status"), False),
        )
