from datetime import datetime, timezone

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField

from app.models.base import BaseModel
from app.models.tenant import Tenant


class Subscriber(BaseModel):
    """
    Stores identity and social authentication state for Mobile Application End-Users bound to a specific Tenant.
    """

    tenant = ForeignKeyField(
        Tenant, column_name="tenant_id", on_delete="CASCADE", index=True, backref="subscribers"
    )
    email = CharField(max_length=255, null=True, index=True)
    name = CharField(max_length=255, null=True)
    avatar_url = CharField(max_length=500, null=True)
    provider = CharField(max_length=50, default="google")  # 'google', 'facebook', or 'guest'
    provider_id = CharField(max_length=255, index=True)  # Google sub, FB id, or Device GUID
    role = CharField(max_length=50, default="subscriber")  # 'subscriber' or 'guest'
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "subscribers"
        indexes = (
            (("tenant", "provider", "provider_id"), True),
        )
