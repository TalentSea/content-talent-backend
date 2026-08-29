from datetime import datetime, timezone

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from playhouse.sqlite_ext import JSONField

from app.models.admin import Admin
from app.models.base import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Stores subscription plan tiers, pricing parameters, discount offers,
    and feature checklists for a white-labeled creator studio.
    """

    user = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="user_id",
        backref="subscription_plans",
        on_delete="CASCADE",
    )
    name = CharField(max_length=100, null=False)
    description = TextField(null=True)
    base_price = FloatField(default=0.0, null=False)
    discount_percentage = FloatField(default=0.0, null=False)
    final_price = FloatField(default=0.0, null=False)
    currency = CharField(max_length=10, default="INR", null=False)
    billing_period_value = IntegerField(default=1, null=False)
    billing_period_unit = CharField(max_length=20, default="months", null=False)
    features = JSONField(default=list)
    badge_text = CharField(max_length=50, null=True)
    is_active = BooleanField(default=True, null=False)
    display_order = IntegerField(default=1, null=False)
    active_subscribers = IntegerField(default=0, null=False)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "subscription_plans"
        indexes = (
            (("user", "display_order"), False),
            (("user", "name"), False),
        )
