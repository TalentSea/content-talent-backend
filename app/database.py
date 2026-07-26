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
    from app.models.video import Video
    from app.models.playlist import Playlist, PlaylistVideo

    if db_proxy.is_closed():
        db_proxy.connect()

    db_proxy.create_tables([User, Video, Playlist, PlaylistVideo], safe=True)

    # Ensure at least one default test user exists for development/auth testing
    if User.select().count() == 0:
        User.create(
            username="default_creator",
            email="creator@example.com"
        )

    if not db_proxy.is_closed():
        db_proxy.close()