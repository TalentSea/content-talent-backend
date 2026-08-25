import logging
import math

from fastapi import HTTPException, status

from app.repositories.admin.comment_repository import CommentRepository
from app.repositories.admin.profile_repository import ProfileRepository
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
        self.profile_repo = ProfileRepository()
        self.video_repo = VideoRepository()

    def _build_author_response(self, c) -> CommentAuthorResponse:
        """Helper to construct canonical CommentAuthorResponse object with real-time profile consistency."""
        if c.user:
            return CommentAuthorResponse(
                id=c.user.id,
                name=c.user.name or f"Subscriber {c.user.id}",
                avatar_url=c.user.avatar_url,
                is_creator=False,
            )
        # For Admin Creator posts where c.user is None
        creator = c.video.user if (c.video and hasattr(c.video, "user")) else None
        creator_id = creator.id if creator else 0
        name = f"{creator.first_name or ''} {creator.last_name or ''}".strip() if creator else "Creator Admin"
        avatar_url = creator.avatar_url if creator else None
        return CommentAuthorResponse(
            id=creator_id, name=name or "Creator Admin", avatar_url=avatar_url, is_creator=True
        )

    def create_top_level_comment(
        self, creator_id: int, video_id: int, payload: CommentReplyCreateRequest
    ) -> CommentItemResponse:
        """
        Posts an official creator top-level comment under a video matching spec doc API 2.
        """
        video = self.video_repo.get_video_by_id(video_id, creator_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} not found",
            )

        creator_user = self.profile_repo.get_profile_by_admin_id(creator_id)
        if not creator_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator account not found",
            )

        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment text cannot be empty",
            )

        comment = self.comment_repo.create_top_level_comment(
            video, creator_user, payload.text.strip()
        )

        creator_name = f"{creator_user.first_name or ''} {creator_user.last_name or ''}".strip() or "Creator Admin"

        return CommentItemResponse(
            id=comment.id,
            text=comment.text,
            author=CommentAuthorResponse(
                id=creator_user.id,
                name=creator_name,
                avatar_url=creator_user.avatar_url,
                is_creator=True,
            ),
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
        creator_id: int,
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
            creator_id=creator_id,
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
        liked_set = self.comment_repo.get_user_liked_comment_ids(
            comment_ids, creator_id
        )

        items: list[CommentItemResponse] = []
        for c in comments:
            reply_count = reply_counts_map.get(c.id, 0)
            is_liked = c.id in liked_set

            item = CommentItemResponse(
                id=c.id,
                text=c.text,
                author=self._build_author_response(c),
                video_id=c.video.id,
                video_title=c.video.title,
                likes=c.likes,
                is_hearted_by_creator=getattr(c, "is_hearted_by_creator", False),
                is_liked=is_liked,
                reply_count=reply_count,
                created_at=c.created_at,
            )
            items.append(item)

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def get_comment_replies(
        self,
        creator_id: int,
        comment_id: int,
        sort: str | None = "oldest",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[CommentReplyResponse]:
        """
        Retrieves paginated child replies nested under a parent comment matching spec doc API 2.
        """
        parent_comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        replies_raw, total = self.comment_repo.get_replies_for_comment(
            comment_id=comment_id, sort=sort, page=page, limit=limit
        )

        reply_ids = [r.id for r in replies_raw]
        liked_set = self.comment_repo.get_user_liked_comment_ids(
            reply_ids, creator_id
        )

        items: list[CommentReplyResponse] = []
        for r in replies_raw:
            is_liked = r.id in liked_set
            items.append(
                CommentReplyResponse(
                    id=r.id,
                    comment_id=parent_comment.id,
                    text=r.text,
                    author=self._build_author_response(r),
                    likes=r.likes or 0,
                    is_hearted_by_creator=getattr(r, "is_hearted_by_creator", False),
                    is_liked=is_liked,
                    created_at=r.created_at,
                )
            )

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def create_reply(
        self, creator_id: int, comment_id: int, payload: CommentReplyCreateRequest
    ) -> CommentReplyCreateResponse:
        """
        Posts an official creator reply to a user comment matching spec doc API 3.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        creator_user = self.profile_repo.get_profile_by_admin_id(creator_id)
        if not creator_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator account not found",
            )

        reply = self.comment_repo.create_reply(comment, creator_user, payload.text)
        creator_name = f"{creator_user.first_name or ''} {creator_user.last_name or ''}".strip() or "Creator Admin"

        return CommentReplyCreateResponse(
            id=reply.id,
            comment_id=reply.parent.id,  # Guarantees root parent ID is returned
            text=reply.text,
            author=CommentAuthorResponse(
                id=creator_user.id,
                name=creator_name,
                avatar_url=creator_user.avatar_url,
                is_creator=True,
            ),
            likes=0,
            is_hearted_by_creator=False,
            is_liked=False,
            created_at=reply.created_at,
        )

    def toggle_comment_like(
        self, creator_id: int, comment_id: int
    ) -> CommentLikeResponse:
        """
        Toggles creator heart state on comment matching spec doc API 4.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        is_hearted, likes = self.comment_repo.toggle_creator_heart(comment)

        return CommentLikeResponse(status="success", is_liked=is_hearted, likes=likes)

    def delete_comment(self, creator_id: int, comment_id: int) -> ActionSuccessResponse:
        """
        Deletes a comment permanently matching spec doc API 5.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        self.comment_repo.delete_comment(comment)

        return ActionSuccessResponse(status="success")
