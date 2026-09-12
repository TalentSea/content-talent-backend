from datetime import datetime, timezone

from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from app.models.admin import Admin
from app.models.base import BaseModel


class Branding(BaseModel):
    """
    Stores public white-label app branding, studio identity, cover banner, and logo for Creator OTT apps.
    """

    user = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="user_id",
        backref="branding",
        unique=True,
        on_delete="CASCADE",
    )
    creator_name = CharField(max_length=255, null=True)
    tagline = CharField(max_length=255, null=True)
    description = TextField(null=True)
    banner_url = CharField(max_length=500, null=True)
    logo_url = CharField(max_length=500, null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "branding"
