import logging
import math

from fastapi import HTTPException, status

from app.repositories.auth_repository import AuthRepository
from app.repositories.mobile_comment_repository import MobileCommentRepository
from app.repositories.mobile_video_repository import MobileVideoRepository
from app.schemas.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.schemas.mobile_comment_schemas import (
    MobileCommentAuthorResponse,
    MobileCommentCreateRequest,
    MobileCommentItemResponse,
    MobileCommentLikeResponse,
    MobileCommentReplyResponse,
)

logger = logging.getLogger(__name__)


class MobileCommentService:
    """
    Business logic service for Mobile Subscriber video comments, thread replies, likes, and deletion matching spec doc.
    """

    def __init__(self):
        self.comment_repo = MobileCommentRepository()
        self.video_repo = MobileVideoRepository()
        self.auth_repo = AuthRepository()

    def _build_author_response(self, c) -> MobileCommentAuthorResponse:
        """Helper to build canonical MobileCommentAuthorResponse object."""
        if c.user:
            return MobileCommentAuthorResponse(
                id=c.user.id,
                name=c.user_name,
                avatar_url=c.user_avatar,
                is_creator=False,
            )
        creator_id = c.video.user.id if (c.video and hasattr(c.video.user, "id")) else 0
        return MobileCommentAuthorResponse(
            id=creator_id, name=c.user_name, avatar_url=c.user_avatar, is_creator=True
        )

    def list_video_comments(
        self,
        video_id: int,
        sort: str | None = "newest",
        page: int = 1,
        limit: int = 20,
        subscriber_id: int | None = None,
    ) -> PaginatedResponse[MobileCommentItemResponse]:
        """
        Retrieves paginated top-level comments for a video matching spec doc API 1.
        """
        video = self.video_repo.get_public_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} not found",
            )

        comments, total = self.comment_repo.get_video_top_level_comments(
            video_id=video_id, sort=sort, page=page, limit=limit
        )

        items: list[MobileCommentItemResponse] = []
        for c in comments:
            reply_count = self.comment_repo.get_reply_count(c.id)
            is_liked = (
                self.comment_repo.is_comment_liked_by_subscriber(c.id, subscriber_id)
                if subscriber_id
                else False
            )
            is_owner = bool(subscriber_id and c.user and c.user.id == subscriber_id)

            items.append(
                MobileCommentItemResponse(
                    id=c.id,
                    text=c.text,
                    author=self._build_author_response(c),
                    likes=c.likes or 0,
                    is_liked=is_liked,
                    reply_count=reply_count,
                    is_owner=is_owner,
                    created_at=c.created_at,
                )
            )

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total, page=page, limit=limit, total_pages=total_pages, items=items
        )

    def create_video_comment(
        self, video_id: int, subscriber_id: int, payload: MobileCommentCreateRequest
    ) -> MobileCommentItemResponse:
        """
        Posts a new top-level comment under a video matching spec doc API 2.
        """
        video = self.video_repo.get_public_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} not found",
            )

        subscriber = self.auth_repo.get_user_by_id(subscriber_id)
        if not subscriber:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscriber account not found",
            )

        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment text cannot be empty",
            )

        comment = self.comment_repo.create_top_level_comment(
            video, subscriber, payload.text.strip()
        )

        return MobileCommentItemResponse(
            id=comment.id,
            text=comment.text,
            author=MobileCommentAuthorResponse(
                id=subscriber.id,
                name=comment.user_name,
                avatar_url=comment.user_avatar,
                is_creator=False,
            ),
            likes=0,
            is_liked=False,
            reply_count=0,
            is_owner=True,
            created_at=comment.created_at,
        )

    def get_comment_replies(
        self,
        comment_id: int,
        sort: str | None = "oldest",
        page: int = 1,
        limit: int = 20,
        subscriber_id: int | None = None,
    ) -> PaginatedResponse[MobileCommentReplyResponse]:
        """
        Retrieves paginated child replies nested under a parent comment matching spec doc API 3.
        """
        parent_comment = self.comment_repo.get_comment_by_id(comment_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        replies_raw, total = self.comment_repo.get_replies_for_comment(
            comment_id=comment_id, sort=sort, page=page, limit=limit
        )

        items: list[MobileCommentReplyResponse] = []
        for r in replies_raw:
            is_liked = (
                self.comment_repo.is_comment_liked_by_subscriber(r.id, subscriber_id)
                if subscriber_id
                else False
            )
            is_owner = bool(subscriber_id and r.user and r.user.id == subscriber_id)

            items.append(
                MobileCommentReplyResponse(
                    id=r.id,
                    comment_id=parent_comment.id,
                    text=r.text,
                    author=self._build_author_response(r),
                    likes=r.likes or 0,
                    is_liked=is_liked,
                    is_owner=is_owner,
                    created_at=r.created_at,
                )
            )

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total, page=page, limit=limit, total_pages=total_pages, items=items
        )

    def create_comment_reply(
        self, comment_id: int, subscriber_id: int, payload: MobileCommentCreateRequest
    ) -> MobileCommentReplyResponse:
        """
        Posts a reply to a comment or sub-comment matching spec doc API 4.
        """
        parent_comment = self.comment_repo.get_comment_by_id(comment_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        subscriber = self.auth_repo.get_user_by_id(subscriber_id)
        if not subscriber:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscriber account not found",
            )

        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reply text cannot be empty",
            )

        reply = self.comment_repo.create_subscriber_reply(
            parent_comment, subscriber, payload.text.strip()
        )

        return MobileCommentReplyResponse(
            id=reply.id,
            comment_id=reply.parent.id,
            text=reply.text,
            author=MobileCommentAuthorResponse(
                id=subscriber.id,
                name=reply.user_name,
                avatar_url=reply.user_avatar,
                is_creator=False,
            ),
            likes=0,
            is_liked=False,
            is_owner=True,
            created_at=reply.created_at,
        )

    def toggle_comment_like(
        self, comment_id: int, subscriber_id: int
    ) -> MobileCommentLikeResponse:
        """
        Toggles subscriber like state on a comment or reply matching spec doc API 5.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        is_liked, likes = self.comment_repo.toggle_like(comment, subscriber_id)

        return MobileCommentLikeResponse(
            status="success", is_liked=is_liked, likes=likes
        )

    def delete_comment(
        self, comment_id: int, subscriber_id: int
    ) -> ActionSuccessResponse:
        """
        Deletes a subscriber's own comment matching spec doc API 6.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        # Ownership verification: subscribers can only delete their own comments!
        if not comment.user or comment.user.id != subscriber_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )

        self.comment_repo.delete_comment(comment)
        return ActionSuccessResponse(status="success")
