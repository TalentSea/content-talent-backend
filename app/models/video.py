from datetime import datetime
from peewee import CharField, TextField, IntegerField, BooleanField, DateTimeField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from app.models.base import BaseModel
from app.models.admin import Admin
from app.models.subscriber import Subscriber

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
    popularity_score = IntegerField(default=0, index=True)
    duration = CharField(max_length=50, null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "videos"

class VideoLike(BaseModel):
    """
    Stores video like relationships between Subscriber and Video entities.
    """
    video = ForeignKeyField(Video, backref="likes", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="video_likes", on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "video_likes"
        indexes = (
            (("video", "subscriber"), True),
        )

class VideoSave(BaseModel):
    """
    Stores video save/bookmark relationships between Subscriber and Video entities ("My Watchlist").
    """
    video = ForeignKeyField(Video, backref="saves", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="video_saves", on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "video_saves"
        indexes = (
            (("video", "subscriber"), True),
        )

def parse_duration_seconds(dur_str) -> int:
    """Safely converts duration string ('02:58', '01:15:30', or 178) into integer seconds."""
    if not dur_str:
        return 0
    if isinstance(dur_str, int):
        return dur_str
    try:
        if ":" in str(dur_str):
            parts = [int(p) for p in str(dur_str).split(":")]
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
        return int(dur_str)
    except Exception:
        return 0

class WatchHistory(BaseModel):
    """
    Stores subscriber playback watch history & resume position for "Continue Watching" carousel.
    """
    video = ForeignKeyField(Video, backref="watch_histories", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, backref="watch_histories", on_delete="CASCADE")
    last_position_seconds = IntegerField(default=0)
    completed = BooleanField(default=False)
    last_watched_at = DateTimeField(default=datetime.now)
    created_at = DateTimeField(default=datetime.now)

    @property
    def completion_percentage(self) -> float:
        """
        Dynamically calculates completion percentage against target video duration.
        """
        try:
            if not self.video or not self.video.duration:
                return 0.0
            dur = parse_duration_seconds(self.video.duration)
            if dur <= 0:
                return 0.0
            pos = self.last_position_seconds or 0
            return round(min(100.0, (pos / float(dur)) * 100.0), 1)
        except Exception:
            return 0.0

    class Meta:
        table_name = "watch_history"
        indexes = (
            (("video", "subscriber"), True),
        )



