import logging
from datetime import date as date_cls
from datetime import datetime, timezone

from peewee import PeeweeException, fn

from app.models.admin import Admin
from app.models.comment import Comment
from app.models.video import Video
from app.utils.date_utils import get_app_timezone

logger = logging.getLogger(__name__)


class CommentRepository:
    """
    Data access layer for Admin Comment operations (Peewee ORM), scoped to Tenant.
    """

    def get_all_comments_by_creator(
        self,
        tenant_id: int,
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
        Retrieves top-level comments for tenant's videos with pagination and filtering.
        """
        try:
            query = (
                Comment.select(Comment, Video)
                .join(Video)
                .where(Video.tenant == tenant_id)
                .where(Comment.parent.is_null(True))
            )

            if video_id:
                query = query.where(Comment.video == video_id)

            if category:
                query = query.where(fn.LOWER(Video.category) == category.lower())

            if date:
                try:
                    target_d = date_cls.fromisoformat(date.strip())
                    tz = get_app_timezone()
                    start_local = datetime(
                        target_d.year, target_d.month, target_d.day, 0, 0, 0, tzinfo=tz
                    )
                    end_local = datetime(
                        target_d.year,
                        target_d.month,
                        target_d.day,
                        23,
                        59,
                        59,
                        999999,
                        tzinfo=tz,
                    )
                    start_utc = start_local.astimezone(timezone.utc)
                    end_utc = end_local.astimezone(timezone.utc)
                    query = query.where(
                        (Comment.created_at >= start_utc)
                        & (Comment.created_at <= end_utc)
                    )
                except (ValueError, TypeError):
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
            logger.error("Error listing comments for tenant %s: %s", tenant_id, e)
            raise

    def get_comment_by_id(self, comment_id: int, tenant_id: int) -> Comment | None:
        """
        Fetches a comment by ID, ensuring it belongs to a video owned by tenant_id.
        """
        try:
            return (
                Comment.select(Comment, Video)
                .join(Video)
                .where(Comment.id == comment_id, Video.tenant == tenant_id)
                .first()
            )
        except PeeweeException as e:
            logger.error("Error fetching comment %s: %s", comment_id, e)
            return None

    def get_batch_reply_counts(self, comment_ids: list[int]) -> dict[int, int]:
        """
        Batches reply counts for a list of parent comment IDs in 1 single query.
        """
        if not comment_ids:
            return {}
        try:
            counts_query = (
                Comment.select(Comment.parent, fn.COUNT(Comment.id).alias("r_count"))
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

    def create_top_level_comment(
        self, video: Video, text: str, creator_user: Admin | None = None
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
        self, parent_comment: Comment, text: str, creator_user: Admin | None = None
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
