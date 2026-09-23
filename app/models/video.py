import json

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.subscriber import Subscriber
from app.models.tenant import Tenant
from app.utils.date_utils import now_utc
from app.utils.formatters import calculate_completion_percentage


class JSONField(TextField):
    """
    Stores structured JSON data as TEXT in SQLite, auto-serializing to/from Python list/dict.
    """

    def db_value(self, value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    def python_value(self, value):
        if value is not None and isinstance(value, str):
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return value
        return value if value is not None else []


class Video(BaseModel):
    """
    Stores metadata for uploaded video entities scoped to a Tenant.
    """

    tenant = ForeignKeyField(
        model=Tenant,
        field=Tenant.id,
        column_name="tenant_id",
        backref="videos",
        on_delete="CASCADE",
        index=True,
    )
    created_by = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="created_by",
        backref="created_videos",
        null=True,
        on_delete="SET NULL",
    )
    bunny_video_id = CharField(unique=True, max_length=255)
    title = CharField(max_length=255, null=False)
    description = TextField(null=False)
    category = CharField(max_length=100, null=True)
    status = CharField(max_length=20, default="processing")
    publish_intent = CharField(
        max_length=20, default="draft"
    )  # 'draft', 'publish', 'schedule'
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
    popularity_score = IntegerField(default=0, index=True)
    duration = CharField(max_length=50, null=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "videos"


class VideoLike(BaseModel):
    """
    Stores video like relationships between Subscriber and Video entities.
    """

    video = ForeignKeyField(Video, backref="likes", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="video_likes", on_delete="CASCADE")
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "video_likes"
        indexes = ((("video", "subscriber"), True),)


class VideoSave(BaseModel):
    """
    Stores video save/bookmark relationships between Subscriber and Video entities ("My Watchlist").
    """

    video = ForeignKeyField(Video, backref="saves", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="video_saves", on_delete="CASCADE")
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "video_saves"
        indexes = ((("video", "subscriber"), True),)


class WatchHistory(BaseModel):
    """
    Stores subscriber playback watch history & resume position for "Continue Watching" carousel.
    """

    video = ForeignKeyField(Video, backref="watch_histories", on_delete="CASCADE")
    subscriber = ForeignKeyField(
        Subscriber, backref="watch_histories", on_delete="CASCADE"
    )
    last_position_seconds = IntegerField(default=0)
    completed = BooleanField(default=False)
    last_watched_at = DateTimeField(default=now_utc)
    created_at = DateTimeField(default=now_utc)

    @property
    def completion_percentage(self) -> float:
        """
        Dynamically calculates completion percentage using centralized formatter helper.
        """
        dur = self.video.duration if self.video else None
        return calculate_completion_percentage(
            self.last_position_seconds, dur, getattr(self, "id", None)
        )

    class Meta:
        table_name = "watch_history"
        indexes = ((("video", "subscriber"), True),)


class VideoViewEvent(BaseModel):
    """
    Immutable event ledger for every validated playback view by an authenticated subscriber.
    Powers tenant telemetry, time-series charts, and windowed analytics.
    Permanent and independent of subscriber personal watch history deletions.
    """

    video = ForeignKeyField(Video, backref="view_events", on_delete="CASCADE")
    tenant = ForeignKeyField(
        model=Tenant,
        column_name="tenant_id",
        backref="view_events",
        on_delete="CASCADE",
        index=True,
    )
    subscriber = ForeignKeyField(Subscriber, backref="view_events", on_delete="CASCADE")
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "video_view_events"
        indexes = (
            (("tenant", "created_at"), False),
            (("video", "created_at"), False),
            (("video", "subscriber", "created_at"), False),
        )
