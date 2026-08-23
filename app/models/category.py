from datetime import datetime, timezone

from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

from app.models.admin import Admin
from app.models.base import BaseModel


class Category(BaseModel):
    """
    Stores category metadata for creator content categorization.
    """

    user = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="user_id",
        backref="categories",
        on_delete="CASCADE",
    )
    name = CharField(max_length=100)
    slug = CharField(max_length=120)
    description = TextField(null=True)
    icon = CharField(max_length=50, default="📁")
    color = CharField(max_length=30, default="#3b82f6")
    display_order = IntegerField(default=0)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "categories"
        indexes = ((("user", "name"), True),)
