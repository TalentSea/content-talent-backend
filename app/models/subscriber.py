from datetime import datetime
from peewee import CharField, DateTimeField, FloatField, ForeignKeyField
from app.models.base import BaseModel
from app.models.user import User

class Subscriber(BaseModel):
    """
    Represents a creator's subscriber record.
    """
    user = ForeignKeyField(
        model=User,
        field=User.id,
        column_name="user_id",
        backref="subscribers",
        on_delete="CASCADE",
    )
    name = CharField(max_length=255)
    email = CharField(max_length=255)
    plan = CharField(max_length=50, default="none")
    status = CharField(max_length=50, default="passive")
    avatar = CharField(max_length=500, default="none")
    revenue = FloatField(default=0.0)
    total_revenue = FloatField(default=0.0)
    joined_at = DateTimeField(default=datetime.now)
    last_active_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "subscribers"
