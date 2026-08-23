import logging

from peewee import IntegrityError, PeeweeException, fn

from app.database import db_proxy
from app.models.comment import Comment, CommentLike
from app.models.subscriber import Subscriber
from app.models.video import Video

logger = logging.getLogger(__name__)


class MobileCommentRepository:
    """
    Data access repository for Mobile Subscriber comment feed, thread replies, likes, and creation.
    """

    def get_video_top_level_comments(
        self, video_id: int, sort: str | None = "newest", page: int = 1, limit: int = 20
    ) -> tuple[list[Comment], int]:
        """
        Retrieves paginated top-level comments for a video (parent is null).
        """
        try:
            query = Comment.select().where(
                (Comment.video == video_id) & (Comment.parent.is_null(True))
            )
            total = query.count()

            if sort == "oldest":
                query = query.order_by(Comment.created_at.asc())
            elif sort == "most_liked":
                query = query.order_by(Comment.likes.desc(), Comment.created_at.desc())
            else:
                query = query.order_by(Comment.created_at.desc())

            comments = list(query.paginate(page, limit))
            return comments, total
        except PeeweeException as e:
            logger.error("Error fetching mobile comments for video %s: %s", video_id, e)
            return [], 0

    def get_comment_by_id(
        self, comment_id: int, creator_id: int | None = None
    ) -> Comment | None:
        """
        Fetches a comment by ID with optional creator_id isolation.
        """
        try:
            query = Comment.select(Comment, Video).join(Video)
            if creator_id is not None:
                query = query.where(
                    (Comment.id == comment_id) & (Video.user == creator_id)
                )
            else:
                query = query.where(Comment.id == comment_id)
            return query.first()
        except PeeweeException as e:
            logger.error("Error fetching comment %s: %s", comment_id, e)
            return None

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

    def get_reply_count(self, comment_id: int) -> int:
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

    def is_comment_liked_by_subscriber(
        self, comment_id: int, subscriber_id: int
    ) -> bool:
        """
        Checks if a subscriber has a row in comment_likes table.
        """
        if not subscriber_id:
            return False
        try:
            return (
                CommentLike.select()
                .where(
                    (CommentLike.comment == comment_id)
                    & (CommentLike.user == subscriber_id)
                )
                .exists()
            )
        except PeeweeException as e:
            logger.error("Error checking like state for comment %s: %s", comment_id, e)
            return False

    def get_subscriber_liked_comment_ids(
        self, comment_ids: list[int], subscriber_id: int | None
    ) -> set[int]:
        """
        Batches liked comment IDs for a subscriber in 1 single query.
        """
        if not comment_ids or not subscriber_id:
            return set()
        try:
            liked_query = CommentLike.select(CommentLike.comment).where(
                (CommentLike.user == subscriber_id)
                & (CommentLike.comment.in_(comment_ids))
            )
            return {row.comment_id for row in liked_query}
        except PeeweeException as e:
            logger.error("Error batch fetching liked comment IDs: %s", e)
            return set()

    def create_top_level_comment(
        self, video: Video, subscriber_id: int, text: str
    ) -> Comment:
        """
        Creates a new top-level comment by a mobile subscriber using raw subscriber_id.
        """
        return Comment.create(
            video=video.id,
            user=subscriber_id,
            text=text,
            parent=None,
        )

    def create_subscriber_reply(
        self, parent_comment: Comment, subscriber_id: int, text: str
    ) -> Comment:
        """
        Creates a new reply nested under the root top-level parent comment.
        """
        root_parent = parent_comment.parent if parent_comment.parent else parent_comment
        return Comment.create(
            video=root_parent.video,
            user=subscriber_id,
            text=text,
            parent=root_parent,
        )

    def toggle_like(self, comment: Comment, subscriber_id: int) -> tuple[bool, int]:
        """
        Toggles like state in comment_likes table for subscriber_id and updates comment.likes.
        """
        try:
            with db_proxy.atomic():
                existing_like = CommentLike.get_or_none(
                    (CommentLike.comment == comment.id)
                    & (CommentLike.user == subscriber_id)
                )

                if existing_like:
                    existing_like.delete_instance()
                    is_liked = False
                else:
                    try:
                        CommentLike.create(comment=comment.id, user=subscriber_id)
                        is_liked = True
                    except IntegrityError:
                        CommentLike.delete().where(
                            (CommentLike.comment == comment.id)
                            & (CommentLike.user == subscriber_id)
                        ).execute()
                        is_liked = False

                total_likes = (
                    CommentLike.select()
                    .where(CommentLike.comment == comment.id)
                    .count()
                )
                comment.likes = total_likes
                comment.save()

                return is_liked, total_likes
        except PeeweeException as e:
            logger.error("Error toggling comment like: %s", e)
            raise

    def delete_comment(self, comment: Comment) -> bool:
        """
        Deletes a comment and its child replies recursively.
        """
        try:
            comment.delete_instance(recursive=True)
            return True
        except PeeweeException as e:
            logger.error("Error deleting comment %s: %s", comment.id, e)
            return False
