from datetime import datetime

from peewee import BooleanField, CharField, DateTimeField

from app.models.base import BaseModel


class Subscriber(BaseModel):
    """
    Stores identity and social authentication state for Mobile Application End-Users.
    """

    email = CharField(max_length=255, null=True, index=True)
    name = CharField(max_length=255, null=True)
    avatar_url = CharField(max_length=500, null=True)
    provider = CharField(max_length=50, default="google")  # 'google' or 'facebook'
    provider_id = CharField(max_length=255, index=True)  # Google sub or Facebook id
    role = CharField(max_length=50, default="subscriber")
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "subscribers"
