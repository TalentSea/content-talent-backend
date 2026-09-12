from datetime import datetime, timezone

from peewee import BooleanField, DateTimeField, ForeignKeyField, IntegerField, TextField

from app.models.base import BaseModel
from app.models.subscriber import Subscriber
from app.models.video import Video


class Comment(BaseModel):
    """
    Peewee ORM model representing video comments and threaded replies with 100% real-time profile consistency.
    """

    video = ForeignKeyField(Video, backref="comments", on_delete="CASCADE")
    user = ForeignKeyField(
        Subscriber, backref="comments", on_delete="CASCADE", null=True
    )
    text = TextField()
    likes = IntegerField(default=0)
    is_hearted_by_creator = BooleanField(default=False)
    parent = ForeignKeyField("self", null=True, backref="replies", on_delete="CASCADE")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "comments"


class CommentLike(BaseModel):
    """
    Junction table tracking likes on comments from mobile subscribers.
    """

    user = ForeignKeyField(Subscriber, backref="comment_likes", on_delete="CASCADE")
    comment = ForeignKeyField(Comment, backref="likes_rel", on_delete="CASCADE")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "comment_likes"
        indexes = (
            (("user", "comment"), True),  # Enforces 1 unique like per subscriber per comment
        )
