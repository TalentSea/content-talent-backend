import logging

from fastapi import HTTPException, status

from app.repositories.admin.comment_repository import CommentRepository
from app.repositories.admin.video_repository import VideoRepository
from app.schemas.admin.comment_schemas import (
    CommentAuthorResponse,
    CommentItemResponse,
    CommentLikeResponse,
    CommentReplyCreateRequest,
    CommentReplyCreateResponse,
    CommentReplyResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse, PaginatedResponse

logger = logging.getLogger(__name__)


class CommentService:
    """
    Business logic service for Creator Comment Moderation, Thread Replies, and Engagement.
    """

    def __init__(self):
        self.comment_repo = CommentRepository()
        self.video_repo = VideoRepository()

    def _build_author_response(self, c) -> CommentAuthorResponse:
        """Helper to construct canonical CommentAuthorResponse object with real-time profile consistency."""
        if c.user:
            return CommentAuthorResponse(
                id=c.user.id,
                name=c.user.name,
                avatar_url=c.user.avatar_url,
                is_creator=False,
            )
        # Official Tenant Studio author
        tenant = c.video.tenant
        return CommentAuthorResponse(
            id=tenant.id,
            name=tenant.name,
            avatar_url=tenant.logo_url,
            is_creator=True,
        )

    def create_top_level_comment(
        self, tenant_id: int, video_id: int, payload: CommentReplyCreateRequest
    ) -> CommentItemResponse:
        """
        Posts an official creator top-level comment under a video matching spec doc API 2.
        """
        video = self.video_repo.get_video_by_id(video_id, tenant_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} not found",
            )

        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment text cannot be empty",
            )

        comment = self.comment_repo.create_top_level_comment(
            video, payload.text.strip()
        )

        return CommentItemResponse(
            id=comment.id,
            text=comment.text,
            author=self._build_author_response(comment),
            video_id=video.id,
            video_title=video.title,
            likes=0,
            is_hearted_by_creator=False,
            is_liked=False,
            reply_count=0,
            created_at=comment.created_at,
        )

    def list_creator_comments(
        self,
        tenant_id: int,
        category: str | None = None,
        video_id: int | None = None,
        date: str | None = None,
        min_likes: int | None = None,
        search: str | None = None,
        sort: str | None = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[CommentItemResponse]:
        """
        Retrieves paginated top-level comments across creator's videos matching spec doc API 1.
        """
        comments, total = self.comment_repo.get_all_comments_by_creator(
            tenant_id=tenant_id,
            search=search,
            video_id=video_id,
            category=category,
            date=date,
            min_likes=min_likes,
            sort=sort,
            page=page,
            limit=limit,
        )

        comment_ids = [c.id for c in comments]
        reply_counts_map = self.comment_repo.get_batch_reply_counts(comment_ids)

        items: list[CommentItemResponse] = []
        for c in comments:
            reply_count = reply_counts_map.get(c.id, 0)
            is_hearted = bool(getattr(c, "is_hearted_by_creator", False))

            item = CommentItemResponse(
                id=c.id,
                text=c.text,
                author=self._build_author_response(c),
                video_id=c.video.id,
                video_title=c.video.title,
                likes=c.likes or 0,
                is_hearted_by_creator=is_hearted,
                is_liked=is_hearted,
                reply_count=reply_count,
                created_at=c.created_at,
            )
            items.append(item)

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def get_comment_replies(
        self,
        tenant_id: int,
        comment_id: int,
        sort: str | None = "oldest",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[CommentReplyResponse]:
        """
        Retrieves paginated child replies nested under a parent comment matching spec doc API 2.
        """
        parent_comment = self.comment_repo.get_comment_by_id(comment_id, tenant_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        replies_raw, total = self.comment_repo.get_replies_for_comment(
            comment_id=comment_id, sort=sort, page=page, limit=limit
        )

        items: list[CommentReplyResponse] = []
        for r in replies_raw:
            is_hearted = bool(getattr(r, "is_hearted_by_creator", False))
            items.append(
                CommentReplyResponse(
                    id=r.id,
                    comment_id=parent_comment.id,
                    text=r.text,
                    author=self._build_author_response(r),
                    likes=r.likes or 0,
                    is_hearted_by_creator=is_hearted,
                    is_liked=is_hearted,
                    created_at=r.created_at,
                )
            )

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def create_reply(
        self, tenant_id: int, comment_id: int, payload: CommentReplyCreateRequest
    ) -> CommentReplyCreateResponse:
        """
        Posts an official creator reply to a user comment matching spec doc API 3.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, tenant_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reply text cannot be empty",
            )

        reply = self.comment_repo.create_reply(comment, payload.text.strip())

        return CommentReplyCreateResponse(
            id=reply.id,
            comment_id=reply.parent.id,  # Guarantees root parent ID is returned
            text=reply.text,
            author=self._build_author_response(reply),
            likes=0,
            is_hearted_by_creator=False,
            is_liked=False,
            created_at=reply.created_at,
        )

    def toggle_comment_like(
        self, tenant_id: int, comment_id: int
    ) -> CommentLikeResponse:
        """
        Toggles creator heart state on comment matching spec doc API 4.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, tenant_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        is_hearted, likes = self.comment_repo.toggle_creator_heart(comment)

        return CommentLikeResponse(status="success", is_liked=is_hearted, likes=likes)

    def delete_comment(self, tenant_id: int, comment_id: int) -> ActionSuccessResponse:
        """
        Deletes a comment permanently matching spec doc API 5.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, tenant_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        self.comment_repo.delete_comment(comment)

        return ActionSuccessResponse(status="success")
