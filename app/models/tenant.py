from peewee import BooleanField, CharField, DateTimeField, TextField

from app.models.base import BaseModel
from app.utils.date_utils import now_utc
from app.utils.string_utils import slugify


class Tenant(BaseModel):
    """
    Unified multi-tenancy and brand entity representing a White-Label Studio / Tenant.
    Stores brand identity, visual assets, and platform operational state.
    """

    name = CharField(max_length=255, unique=True, index=True)
    slug = CharField(max_length=255, unique=True, index=True)
    tagline = CharField(max_length=255, null=True)
    description = TextField(null=True)
    logo_url = CharField(max_length=500, null=True)
    banner_url = CharField(max_length=500, null=True)
    twitter_url = CharField(max_length=255, null=True)
    youtube_url = CharField(max_length=255, null=True)
    instagram_url = CharField(max_length=255, null=True)
    is_active = BooleanField(default=True, index=True)
    deactivation_reason = TextField(null=True)
    deactivated_at = DateTimeField(null=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    class Meta:
        table_name = "tenants"
