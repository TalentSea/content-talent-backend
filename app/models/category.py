import uuid
from datetime import datetime
from peewee import CharField, IntegerField, DateTimeField
from app.models.base import BaseModel

def generate_uuid():
    return str(uuid.uuid4())

class Category(BaseModel):
    id = CharField(primary_key=True, default=generate_uuid, max_length=50)
    name = CharField(max_length=255, unique=True)
    description = CharField(max_length=500, null=True)
    icon = CharField(max_length=50, null=True)
    color = CharField(max_length=20, null=True)
    order = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "categories"
