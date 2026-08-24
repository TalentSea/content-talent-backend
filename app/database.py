from peewee import DatabaseProxy, SqliteDatabase

from app.config import get_settings

# Global database proxy for Peewee ORM
db_proxy = DatabaseProxy()


def init_db():
    """
    Initializes Peewee SQLite database connection with foreign key enforcement and JSON support.
    """
    settings = get_settings()
    db = SqliteDatabase(
        settings.SQLITE_DB_PATH,
        timeout=30,
        pragmas={
            "foreign_keys": 1,
            "journal_mode": "wal",
            "synchronous": "normal",
            "busy_timeout": 30000,
        },
    )
    db_proxy.initialize(db)

    # Import models here to prevent circular dependency
    from app.models.admin import Admin
    from app.models.branding import Branding
    from app.models.category import Category
    from app.models.comment import Comment, CommentLike
    from app.models.featured_video import FeaturedVideo
    from app.models.playlist import Playlist, PlaylistVideo
    from app.models.refresh_token import RefreshToken
    from app.models.subscriber import Subscriber
    from app.models.video import Video, VideoLike, VideoSave, WatchHistory

    if db_proxy.is_closed():
        db_proxy.connect()

    db_proxy.create_tables(
        [
            Admin,
            Branding,
            Subscriber,
            RefreshToken,
            Video,
            VideoLike,
            VideoSave,
            WatchHistory,
            Playlist,
            PlaylistVideo,
            Comment,
            CommentLike,
            Category,
            FeaturedVideo,
        ],
        safe=True,
    )

    # Ensure at least one default test creator exists in admins table for development/auth testing
    if Admin.select().count() == 0:
        Admin.create(
            email="creator@example.com",
            first_name="Creator",
            last_name="Name",
            bio="Content creator and educator",
            website="https://example.com",
            phone="+1 (555) 123-4567",
            location="San Francisco, CA",
            twitter_url="https://twitter.com/username",
            youtube_url="https://youtube.com/@username",
            instagram_url="https://instagram.com/username",
        )

    if not db_proxy.is_closed():
        db_proxy.close()
