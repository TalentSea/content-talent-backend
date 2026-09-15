from datetime import datetime, timezone

from peewee import DateTimeField, ForeignKeyField, IntegerField

from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.video import Video


class FeaturedVideo(BaseModel):
    """
    Peewee ORM entity representing creator home screen carousel featured video curation.
    """

    creator = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="creator_id",
        backref="featured_videos",
        on_delete="CASCADE",
    )
    video = ForeignKeyField(
        model=Video,
        field=Video.id,
        column_name="video_id",
        backref="featured_in",
        on_delete="CASCADE",
    )
    position = IntegerField(default=0, index=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "featured_videos"
        indexes = (
            (("creator", "video"), True),  # Unique entry per video per creator studio
        )
