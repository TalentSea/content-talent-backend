from datetime import datetime, timezone

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField

from app.models.base import BaseModel
from app.models.subscriber import Subscriber


class RefreshToken(BaseModel):
    """
    Stores active hashed JWT refresh tokens for mobile subscriber session management, token rotation, and logout revocation.
    """

    user = ForeignKeyField(
        model=Subscriber,
        field=Subscriber.id,
        column_name="user_id",
        backref="refresh_tokens",
        on_delete="CASCADE",
    )
    token_hash = CharField(unique=True, max_length=255, index=True)
    device_info = CharField(max_length=255, null=True)
    expires_at = DateTimeField(index=True)
    is_revoked = BooleanField(default=False)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "refresh_tokens"
