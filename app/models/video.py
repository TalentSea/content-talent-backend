from datetime import datetime, timezone

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from playhouse.sqlite_ext import JSONField

from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.subscriber import Subscriber
from app.utils.formatters import calculate_completion_percentage


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
    title = CharField(max_length=255, null=False)
    description = TextField(null=False)
    category = CharField(max_length=100, null=False)
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
    popularity_score = IntegerField(default=0, index=True)
    duration = CharField(max_length=50, null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "videos"


class VideoLike(BaseModel):
    """
    Stores video like relationships between Subscriber and Video entities.
    """

    video = ForeignKeyField(Video, backref="likes", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="video_likes", on_delete="CASCADE")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "video_likes"
        indexes = ((("video", "subscriber"), True),)


class VideoSave(BaseModel):
    """
    Stores video save/bookmark relationships between Subscriber and Video entities ("My Watchlist").
    """

    video = ForeignKeyField(Video, backref="saves", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="video_saves", on_delete="CASCADE")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

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
    last_watched_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

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
