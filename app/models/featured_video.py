from peewee import DateTimeField, ForeignKeyField, IntegerField

from app.models.base import BaseModel
from app.models.tenant import Tenant
from app.models.video import Video
from app.utils.date_utils import now_utc


class FeaturedVideo(BaseModel):
    """
    Peewee ORM entity representing tenant home screen carousel featured video curation.
    """

    tenant = ForeignKeyField(
        model=Tenant,
        field=Tenant.id,
        column_name="tenant_id",
        backref="featured_videos",
        on_delete="CASCADE",
        index=True,
    )
    video = ForeignKeyField(
        model=Video,
        field=Video.id,
        column_name="video_id",
        backref="featured_in",
        on_delete="CASCADE",
        index=True,
    )
    position = IntegerField(default=0, index=True)
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "featured_videos"
        indexes = (
            (("tenant", "video"), True),  # Unique entry per video per tenant studio
        )
