from peewee import (
    CharField,
    CompositeKey,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.subscriber import Subscriber
from app.models.tenant import Tenant
from app.models.video import Video
from app.utils.date_utils import now_utc


class Playlist(BaseModel):
    """
    Container for custom video collections owned by a Tenant.
    """

    tenant = ForeignKeyField(
        model=Tenant,
        field=Tenant.id,
        column_name="tenant_id",
        backref="playlists",
        on_delete="CASCADE",
        index=True,
    )
    created_by = ForeignKeyField(
        model=Admin,
        field=Admin.id,
        column_name="created_by",
        backref="created_playlists",
        null=True,
        on_delete="SET NULL",
    )
    name = CharField(max_length=255)
    description = TextField(null=True)
    thumbnail_url = CharField(max_length=500, null=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "playlists"


class PlaylistVideo(BaseModel):
    """
    Junction table linking Playlists and Videos in a Many-to-Many structure.
    """

    playlist = ForeignKeyField(
        model=Playlist,
        field=Playlist.id,
        column_name="playlist_id",
        backref="playlist_videos",
        on_delete="CASCADE",
    )
    video = ForeignKeyField(
        model=Video,
        field=Video.id,
        column_name="video_id",
        backref="playlist_videos",
        on_delete="CASCADE",
    )
    order = IntegerField(default=0)
    added_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "playlist_videos"
        primary_key = CompositeKey("playlist", "video")


class PlaylistSave(BaseModel):
    """
    Stores playlist bookmark/save relationships between Subscriber and Playlist entities.
    """

    playlist = ForeignKeyField(
        model=Playlist,
        field=Playlist.id,
        column_name="playlist_id",
        backref="saves",
        on_delete="CASCADE",
    )
    subscriber = ForeignKeyField(
        model=Subscriber,
        field=Subscriber.id,
        column_name="subscriber_id",
        backref="playlist_saves",
        on_delete="CASCADE",
    )
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "playlist_saves"
        indexes = ((("playlist", "subscriber"), True),)
