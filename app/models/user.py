from datetime import datetime
from peewee import CharField, TextField, DateTimeField
from app.models.base import BaseModel

class User(BaseModel):
    """
    Stores identity, authentication state, and token management attributes.
    """
    username = CharField(unique=True, max_length=100)
    email = CharField(unique=True, max_length=255)
    refresh_token = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "users"
