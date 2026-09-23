from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

from app.config import get_settings
from app.models.base import BaseModel
from app.models.tenant import Tenant
from app.utils.date_utils import now_utc


class Category(BaseModel):
    """
    Stores category metadata for tenant content categorization.
    """

    tenant = ForeignKeyField(
        model=Tenant,
        field=Tenant.id,
        column_name="tenant_id",
        backref="categories",
        on_delete="CASCADE",
        index=True,
    )
    name = CharField(max_length=100)
    slug = CharField(max_length=120)
    description = TextField(null=True)
    thumbnail_url = CharField(max_length=500, null=True)
    color = CharField(
        max_length=30, default=lambda: get_settings().DEFAULT_CATEGORY_COLOR
    )
    display_order = IntegerField(default=0)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "categories"
        indexes = ((("tenant", "name"), True),)
