from datetime import datetime, timezone

from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
)

from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.payment import Payment
from app.models.subscriber import Subscriber
from app.models.subscription_plan import SubscriptionPlan


class UserSubscription(BaseModel):
    """
    Stores active member entitlements and access validity periods
    for subscribers enrolled under a specific creator studio.
    """

    user = ForeignKeyField(
        model=Subscriber,
        field=Subscriber.id,
        column_name="user_id",
        backref="user_subscriptions",
        on_delete="CASCADE",
    )
    creator = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="creator_id",
        backref="creator_subscriptions",
        on_delete="CASCADE",
    )
    plan = ForeignKeyField(
        model=SubscriptionPlan,
        field=SubscriptionPlan.id,
        column_name="plan_id",
        backref="plan_subscriptions",
        on_delete="RESTRICT",
    )
    payment = ForeignKeyField(
        model=Payment,
        field=Payment.id,
        column_name="payment_id",
        backref="payment_subscription",
        null=True,
        on_delete="SET NULL",
    )
    start_date = DateTimeField(default=lambda: datetime.now(timezone.utc))
    end_date = DateTimeField(index=True, null=False)
    status = CharField(max_length=30, default="active", index=True, null=False)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "user_subscriptions"
        indexes = (
            (("user", "creator", "status"), False),
            (("end_date", "status"), False),
        )
