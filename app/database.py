from peewee import DatabaseProxy, SqliteDatabase
from playhouse.sqlite_ext import SqliteExtDatabase
from app.config import get_settings

# Global database proxy for Peewee ORM
db_proxy = DatabaseProxy()

def init_db():
    """
    Initializes Peewee SQLite database connection with foreign key enforcement and JSON support.
    """
    settings = get_settings()
    pass