from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    TextField,
)

from app.models.base import BaseModel
from app.models.tenant import Tenant
from app.utils.date_utils import now_utc
from app.utils.string_utils import format_full_name


class Admin(BaseModel):
    """
    Stores identity, authentication state, creator profile attributes, and permissions for Web Admin Panel users.
    Belongs to a Tenant (nullable for platform-wide Super Admin).
    """

    tenant = ForeignKeyField(
        Tenant,
        column_name="tenant_id",
        null=True,
        backref="admins",
        on_delete="CASCADE",
        index=True,
    )
    role = CharField(max_length=30, default="admin")  # 'admin' or 'super_admin'
    is_owner = BooleanField(default=False)
    email = CharField(unique=True, max_length=255, index=True)
    password_hash = CharField(max_length=255, null=True)
    first_name = CharField(max_length=100, null=False)
    last_name = CharField(max_length=100, null=False)
    phone = CharField(max_length=50, null=True)
    location = CharField(max_length=255, null=True)
    bio = TextField(null=True)
    website = CharField(max_length=255, null=True)
    avatar_url = CharField(max_length=500, null=True)
    refresh_token = TextField(null=True)
    is_active = BooleanField(default=True, index=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    @property
    def name(self) -> str:
        """
        Returns full admin name (first_name + last_name).
        """
        return format_full_name(self.first_name, self.last_name)

    class Meta:
        table_name = "admins"
