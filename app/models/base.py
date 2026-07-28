from peewee import Model
from app.database import db_proxy

class BaseModel(Model):
    """
    Base Peewee model setting the global database connection for all tables.
    """
    class Meta:
        database = db_proxy
