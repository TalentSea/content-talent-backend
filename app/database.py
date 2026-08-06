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
        pragmas={
            'foreign_keys': 1,
            'journal_mode': 'wal',
            'synchronous': 'normal'
        }
    )
    db_proxy.initialize(db)

    # Import models here to prevent circular dependency
    from app.models.user import User
    from app.models.refresh_token import RefreshToken
    from app.models.video import Video
    from app.models.playlist import Playlist, PlaylistVideo
    from app.models.comment import Comment, CommentLike

    if db_proxy.is_closed():
        db_proxy.connect()

    db_proxy.create_tables([User, RefreshToken, Video, Playlist, PlaylistVideo, Comment, CommentLike], safe=True)

    # Ensure at least one default test user exists for development/auth testing
    if User.select().count() == 0:
        User.create(
            username="default_creator",
            email="creator@example.com",
            first_name="Creator",
            last_name="Name",
            bio="Content creator and educator",
            website="https://example.com",
            phone="+1 (555) 123-4567",
            location="San Francisco, CA",
            twitter_url="https://twitter.com/username",
            youtube_url="https://youtube.com/@username",
            instagram_url="https://instagram.com/username"
        )

    if not db_proxy.is_closed():
        db_proxy.close()