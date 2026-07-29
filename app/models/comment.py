from datetime import datetime
from peewee import ForeignKeyField, CharField, TextField, IntegerField, DateTimeField
from app.models.base import BaseModel
from app.models.user import User
from app.models.video import Video

class Comment(BaseModel):
    """
    Peewee ORM model representing video comments and threaded replies.
    """
    video = ForeignKeyField(Video, backref='comments', on_delete='CASCADE')
    user = ForeignKeyField(User, backref='comments', on_delete='CASCADE')
    user_name = CharField(max_length=100)
    user_avatar = CharField(max_length=500, null=True)
    text = TextField()
    likes = IntegerField(default=0)
    parent = ForeignKeyField('self', null=True, backref='replies', on_delete='CASCADE')
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "comments"

class CommentLike(BaseModel):
    """
    Junction table tracking likes/hearts on comments from users (creators & subscribers).
    """
    user = ForeignKeyField(User, backref='comment_likes', on_delete='CASCADE')
    comment = ForeignKeyField(Comment, backref='likes_rel', on_delete='CASCADE')
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "comment_likes"
        indexes = (
            (('user', 'comment'), True),  # Enforces 1 unique like per user per comment
        )
