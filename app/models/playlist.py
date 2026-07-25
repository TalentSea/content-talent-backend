from datetime import datetime
from peewee import CharField, TextField, IntegerField, DateTimeField, ForeignKeyField, CompositeKey
from app.models.base import BaseModel
from app.models.user import User
from app.models.video import Video

class Playlist(BaseModel):
    """
    Container for custom video collections owned by a User.
    """
    user = ForeignKeyField(
        model=User,
        field=User.id,
        column_name="user_id",
        backref="playlists",
        on_delete="CASCADE",
    )
    name = CharField(max_length=255)
    description = TextField(null=True)
    thumbnail_url = CharField(max_length=500, null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

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
    added_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "playlist_videos"
        primary_key = CompositeKey("playlist", "video")
