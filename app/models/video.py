from datetime import datetime
from peewee import CharField, TextField, IntegerField, BooleanField, DateTimeField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from app.models.base import BaseModel
from app.models.admin import Admin

class Video(BaseModel):
    """
    Stores metadata for uploaded video entities.
    """
    user = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="user_id",
        backref="videos",
        on_delete="CASCADE",
    )
    bunny_video_id = CharField(unique=True, max_length=255)
    title = CharField(max_length=255)
    description = TextField(null=True)
    category = CharField(max_length=100, null=True)
    status = CharField(max_length=20, default="PENDING")
    encode_progress = IntegerField(default=0)
    is_playable = BooleanField(default=False)
    main_thumbnail_url = CharField(max_length=500, null=True)
    captions_data = JSONField(default=list)
    available_resolutions = JSONField(default=list)
    tags = JSONField(default=list)
    alt_thumbnail_urls = JSONField(default=list)
    scheduled_at = DateTimeField(null=True)
    published_at = DateTimeField(null=True)
    views = IntegerField(default=0)
    duration = CharField(max_length=50, null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "videos"
