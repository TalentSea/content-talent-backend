from datetime import datetime
from peewee import CharField, TextField, FloatField, BooleanField, DateTimeField, ForeignKeyField
from app.models.base import BaseModel
from app.models.user import User

class Plan(BaseModel):
    """
    Represents a subscription plan available on the platform.
    """
    user = ForeignKeyField(
        model=User,
        field=User.id,
        column_name="user_id",
        backref="plans",
        on_delete="CASCADE",
    )
    name = CharField(max_length=255)
    price = FloatField(default=0.0)
    period = CharField(max_length=20, default="month")
    description = TextField(null=True)
    features = TextField(null=True)
    active = BooleanField(default=True)
    popular = BooleanField(default=False)
    subscribers = FloatField(default=0.0)
    monthly_revenue = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "plans"
