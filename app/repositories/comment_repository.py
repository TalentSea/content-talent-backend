import logging

from peewee import IntegrityError, PeeweeException, fn

from app.database import db_proxy
from app.models.admin import Admin
from app.models.comment import Comment, CommentLike
from app.models.video import Video

logger = logging.getLogger(__name__)


class CommentRepository:
    """
    Data access layer for Admin Comment operations (Peewee ORM).
    """

    def get_all_comments_by_creator(
        self,
        creator_id: int,
        search: str | None = None,
        video_id: int | None = None,
        category: str | None = None,
        date: str | None = None,
        min_likes: int | None = None,
        sort: str | None = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Comment], int]:
        """
        Retrieves top-level comments for creator's videos with pagination and filtering.
        """
        try:
            query = (
                Comment.select(Comment, Video)
                .join(Video)
                .where(Video.user == creator_id)
                .where(Comment.parent.is_null(True))
            )

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
            logger.error("Error listing comments for creator %s: %s", creator_id, e)
            raise

    def get_comment_by_id(self, comment_id: int, creator_id: int) -> Comment | None:
        """
        Fetches a comment by ID, ensuring it belongs to a video owned by creator_id.
        """
        try:
            return (
                Comment.select(Comment, Video)
                .join(Video)
                .where(Comment.id == comment_id, Video.user == creator_id)
                .first()
            )
        except PeeweeException as e:
            logger.error("Error fetching comment %s: %s", comment_id, e)
            return None

    def get_reply_count_for_comment(self, comment_id: int) -> int:
        """
        Counts total replies nested under a parent comment.
        """
        try:
            return Comment.select().where(Comment.parent == comment_id).count()
        except PeeweeException as e:
            logger.error("Error counting replies for comment %s: %s", comment_id, e)
            return 0

    def get_batch_reply_counts(self, comment_ids: list[int]) -> dict[int, int]:
        """
        Batches reply counts for a list of parent comment IDs in 1 single query.
        """
        if not comment_ids:
            return {}
        try:
            counts_query = (
                Comment.select(
                    Comment.parent, fn.COUNT(Comment.id).alias("r_count")
                )
                .where(Comment.parent.in_(comment_ids))
                .group_by(Comment.parent)
            )
            return {row.parent_id: row.r_count for row in counts_query}
        except PeeweeException as e:
            logger.error("Error batch fetching reply counts: %s", e)
            return {}

    def get_replies_for_comment(
        self,
        comment_id: int,
        sort: str | None = "oldest",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Comment], int]:
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
            logger.error("Error fetching replies for comment %s: %s", comment_id, e)
            return [], 0

    def is_comment_liked_by_user(self, comment_id: int, user_id: int) -> bool:
        """
        Checks if a specific user has a row in comment_likes table.
        """
        try:
            return (
                CommentLike.select()
                .where(
                    (CommentLike.comment == comment_id) & (CommentLike.user == user_id)
                )
                .exists()
            )
        except PeeweeException as e:
            logger.error("Error checking like state for comment %s: %s", comment_id, e)
            return False

    def get_user_liked_comment_ids(
        self, comment_ids: list[int], user_id: int | None
    ) -> set[int]:
        """
        Batches liked comment IDs for a user in 1 single query.
        """
        if not comment_ids or not user_id:
            return set()
        try:
            liked_query = CommentLike.select(CommentLike.comment).where(
                (CommentLike.user == user_id) & (CommentLike.comment.in_(comment_ids))
            )
            return {row.comment_id for row in liked_query}
        except PeeweeException as e:
            logger.error("Error batch fetching liked comment IDs: %s", e)
            return set()

    def create_top_level_comment(
        self, video: Video, creator_user: Admin, text: str
    ) -> Comment:
        """
        Creates a creator top-level comment under a video (user=None represents Creator Admin).
        """
        return Comment.create(
            video=video,
            user=None,
            text=text,
            parent=None,
        )

    def create_reply(
        self, parent_comment: Comment, creator_user: Admin, text: str
    ) -> Comment:
        """
        Creates a creator reply nested under the root top-level parent comment (user=None represents Creator Admin).
        """
        root_parent = parent_comment.parent if parent_comment.parent else parent_comment
        reply = Comment.create(
            video=root_parent.video,
            user=None,
            text=text,
            parent=root_parent,
        )
        return reply

    def toggle_creator_heart(self, comment: Comment) -> tuple[bool, int]:
        """
        Toggles is_hearted_by_creator boolean flag on a comment.
        """
        comment.is_hearted_by_creator = not comment.is_hearted_by_creator
        comment.save()
        return comment.is_hearted_by_creator, comment.likes

    def delete_comment(self, comment: Comment) -> bool:
        """
        Deletes a comment and all nested replies from database.
        """
        comment.delete_instance(recursive=True)
        return True
