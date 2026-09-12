from datetime import datetime, timezone

from peewee import CharField, DateTimeField, TextField

from app.models.base import BaseModel


class Admin(BaseModel):
    """
    Stores identity, authentication state, creator profile attributes, and social media handles for Web Admin Panel users.
    """

    email = CharField(unique=True, max_length=255, index=True)
    first_name = CharField(max_length=100, null=True)
    last_name = CharField(max_length=100, null=True)
    phone = CharField(max_length=50, null=True)
    location = CharField(max_length=255, null=True)
    bio = TextField(null=True)
    website = CharField(max_length=255, null=True)
    avatar_url = CharField(max_length=500, null=True)
    twitter_url = CharField(max_length=255, null=True)
    youtube_url = CharField(max_length=255, null=True)
    instagram_url = CharField(max_length=255, null=True)
    refresh_token = TextField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "admins"
