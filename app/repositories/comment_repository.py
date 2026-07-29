import logging
from typing import Optional, List, Tuple
from peewee import PeeweeException, fn

from app.models.comment import Comment, CommentLike
from app.models.video import Video
from app.models.user import User

logger = logging.getLogger(__name__)

class CommentRepository:
    """
    Data access layer for Admin Comment operations (Peewee ORM).
    """

    def get_all_comments_by_creator(
        self,
        creator_id: int,
        search: Optional[str] = None,
        video_id: Optional[int] = None,
        category: Optional[str] = None,
        date: Optional[str] = None,
        min_likes: Optional[int] = None,
        sort: Optional[str] = "newest",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Comment], int]:
        """
        Retrieves top-level comments for creator's videos with pagination and filtering.
        """
        try:
            query = (Comment
                     .select(Comment, Video, User)
                     .join(Video)
                     .switch(Comment)
                     .join(User)
                     .where(Video.user == creator_id)
                     .where(Comment.parent.is_null(True)))

            if video_id:
                query = query.where(Comment.video == video_id)

            if category:
                query = query.where(Video.category == category)

            if date:
                query = query.where(fn.date(Comment.created_at) == date)

            if search:
                query = query.where(Comment.text.contains(search))

            if min_likes is not None:
                query = query.where(Comment.likes >= min_likes)

            total = query.count()

            # Sorting
            if sort == "oldest":
                query = query.order_by(Comment.created_at.asc())
            elif sort == "mostLiked":
                query = query.order_by(Comment.likes.desc(), Comment.created_at.desc())
            else:
                query = query.order_by(Comment.created_at.desc())

            comments = list(query.paginate(page, limit))
            return comments, total

        except PeeweeException as e:
            logger.error(f"Error listing comments for creator {creator_id}: {str(e)}")
            raise e

    def get_comment_by_id(self, comment_id: int, creator_id: int) -> Optional[Comment]:
        """
        Fetches a comment by ID, ensuring it belongs to a video owned by creator_id.
        """
        try:
            return (Comment
                    .select(Comment, Video)
                    .join(Video)
                    .where(Comment.id == comment_id, Video.user == creator_id)
                    .first())
        except PeeweeException as e:
            logger.error(f"Error fetching comment {comment_id}: {str(e)}")
            return None

    def get_reply_count_for_comment(self, comment_id: int) -> int:
        """
        Counts total replies nested under a parent comment.
        """
        try:
            return Comment.select().where(Comment.parent == comment_id).count()
        except PeeweeException as e:
            logger.error(f"Error counting replies for comment {comment_id}: {str(e)}")
            return 0

    def get_replies_for_comment(
        self,
        comment_id: int,
        sort: Optional[str] = "oldest",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Comment], int]:
        """
        Fetches paginated child replies nested under a parent comment.
        """
        try:
            query = Comment.select().where(Comment.parent == comment_id)
            total = query.count()

            if sort == "newest":
                query = query.order_by(Comment.created_at.desc())
            else:
                query = query.order_by(Comment.created_at.asc())

            replies = list(query.paginate(page, limit))
            return replies, total
        except PeeweeException as e:
            logger.error(f"Error fetching replies for comment {comment_id}: {str(e)}")
            return [], 0

    def is_comment_liked_by_user(self, comment_id: int, user_id: int) -> bool:
        """
        Checks if a specific user has a row in comment_likes table.
        """
        try:
            return CommentLike.select().where(
                (CommentLike.comment == comment_id) & (CommentLike.user == user_id)
            ).exists()
        except PeeweeException as e:
            logger.error(f"Error checking like state for comment {comment_id}: {str(e)}")
            return False

    def create_reply(self, parent_comment: Comment, creator_user: User, text: str) -> Comment:
        """
        Creates a creator reply nested under the root top-level parent comment.
        """
        root_parent = parent_comment.parent if parent_comment.parent else parent_comment
        creator_name = f"{creator_user.first_name or ''} {creator_user.last_name or ''}".strip() or creator_user.username
        reply = Comment.create(
            video=root_parent.video,
            user=creator_user,
            user_name=creator_name,
            user_avatar=creator_user.avatar_url,
            text=text,
            parent=root_parent
        )
        return reply

    def toggle_like(self, comment: Comment, user_id: int) -> Tuple[bool, int]:
        """
        Toggles like state in comment_likes table for user_id and updates comment.likes.
        """
        try:
            existing_like = CommentLike.get_or_none(
                (CommentLike.comment == comment.id) & (CommentLike.user == user_id)
            )

            if existing_like:
                existing_like.delete_instance()
                is_liked = False
            else:
                CommentLike.create(comment=comment.id, user=user_id)
                is_liked = True

            total_likes = CommentLike.select().where(CommentLike.comment == comment.id).count()
            comment.likes = total_likes
            comment.save()

            return is_liked, total_likes

        except PeeweeException as e:
            logger.error(f"Error toggling like for user {user_id} on comment {comment.id}: {str(e)}")
            raise e

    def delete_comment(self, comment: Comment) -> bool:
        """
        Deletes a comment and all nested replies from database.
        """
        comment.delete_instance(recursive=True)
        return True
