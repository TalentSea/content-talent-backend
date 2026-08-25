import logging
import math

from fastapi import HTTPException, status

from app.repositories.mobile.auth_repository import AuthRepository
from app.repositories.mobile.comment_repository import MobileCommentRepository
from app.repositories.mobile.video_repository import MobileVideoRepository
from app.schemas.shared.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.schemas.mobile.comment_schemas import (
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
                name=c.user.name or f"Subscriber {c.user.id}",
                avatar_url=c.user.avatar_url,
                is_creator=False,
            )
        creator = c.video.user if (c.video and hasattr(c.video, "user")) else None
        return MobileCommentAuthorResponse(
            id=creator.id if creator else 0,
            name=creator.name if creator else "Admin Creator",
            avatar_url=creator.avatar_url if creator else None,
            is_creator=True,
        )

    def list_video_comments(
        self,
        video_id: int,
        sort: str | None = "newest",
        page: int = 1,
        limit: int = 20,
        subscriber_id: int | None = None,
        creator_id: int | None = None,
    ) -> PaginatedResponse[MobileCommentItemResponse]:
        """
        Retrieves paginated top-level comments for a video matching spec doc API 1.
        """
        video = self.video_repo.get_public_video_by_id(video_id, creator_id=creator_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} not found",
            )

        comments, total = self.comment_repo.get_video_top_level_comments(
            video_id=video_id, sort=sort, page=page, limit=limit
        )

        comment_ids = [c.id for c in comments]
        reply_counts_map = self.comment_repo.get_batch_reply_counts(comment_ids)
        liked_set = self.comment_repo.get_subscriber_liked_comment_ids(
            comment_ids, subscriber_id
        )

        items: list[MobileCommentItemResponse] = []
        for c in comments:
            reply_count = reply_counts_map.get(c.id, 0)
            is_liked = c.id in liked_set
            is_owner = bool(subscriber_id and c.user and c.user.id == subscriber_id)

            items.append(
                MobileCommentItemResponse(
                    id=c.id,
                    text=c.text,
                    author=self._build_author_response(c),
                    likes=c.likes or 0,
                    is_hearted_by_creator=getattr(c, "is_hearted_by_creator", False),
                    is_liked=is_liked,
                    reply_count=reply_count,
                    is_owner=is_owner,
                    created_at=c.created_at,
                )
            )

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def create_video_comment(
        self,
        video_id: int,
        subscriber_id: int,
        payload: MobileCommentCreateRequest,
        creator_id: int | None = None,
    ) -> MobileCommentItemResponse:
        """
        Posts a new top-level comment under a video matching spec doc API 2.
        """
        video = self.video_repo.get_public_video_by_id(video_id, creator_id=creator_id)
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
            video, subscriber_id, payload.text.strip()
        )

        return MobileCommentItemResponse(
            id=comment.id,
            text=comment.text,
            author=self._build_author_response(comment),
            likes=0,
            is_hearted_by_creator=False,
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
        creator_id: int | None = None,
    ) -> PaginatedResponse[MobileCommentReplyResponse]:
        """
        Retrieves paginated child replies nested under a parent comment matching spec doc API 3.
        """
        parent_comment = self.comment_repo.get_comment_by_id(
            comment_id, creator_id=creator_id
        )
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        replies_raw, total = self.comment_repo.get_replies_for_comment(
            comment_id=comment_id, sort=sort, page=page, limit=limit
        )

        reply_ids = [r.id for r in replies_raw]
        liked_set = self.comment_repo.get_subscriber_liked_comment_ids(
            reply_ids, subscriber_id
        )

        items: list[MobileCommentReplyResponse] = []
        for r in replies_raw:
            is_liked = r.id in liked_set
            is_owner = bool(subscriber_id and r.user and r.user.id == subscriber_id)

            items.append(
                MobileCommentReplyResponse(
                    id=r.id,
                    comment_id=parent_comment.id,
                    text=r.text,
                    author=self._build_author_response(r),
                    likes=r.likes or 0,
                    is_hearted_by_creator=getattr(r, "is_hearted_by_creator", False),
                    is_liked=is_liked,
                    is_owner=is_owner,
                    created_at=r.created_at,
                )
            )

        return PaginatedResponse.create(
            items=items, total=total, page=page, limit=limit
        )

    def create_comment_reply(
        self,
        comment_id: int,
        subscriber_id: int,
        payload: MobileCommentCreateRequest,
        creator_id: int | None = None,
    ) -> MobileCommentReplyResponse:
        """
        Posts a reply to a comment or sub-comment matching spec doc API 4.
        """
        parent_comment = self.comment_repo.get_comment_by_id(
            comment_id, creator_id=creator_id
        )
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )

        if not payload.text or not payload.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reply text cannot be empty",
            )

        reply = self.comment_repo.create_subscriber_reply(
            parent_comment, subscriber_id, payload.text.strip()
        )

        return MobileCommentReplyResponse(
            id=reply.id,
            comment_id=reply.parent.id,
            text=reply.text,
            author=self._build_author_response(reply),
            likes=0,
            is_hearted_by_creator=False,
            is_liked=False,
            is_owner=True,
            created_at=reply.created_at,
        )

    def toggle_comment_like(
        self, comment_id: int, subscriber_id: int, creator_id: int | None = None
    ) -> MobileCommentLikeResponse:
        """
        Toggles subscriber like state on a comment or reply matching spec doc API 5.
        """
        comment = self.comment_repo.get_comment_by_id(
            comment_id, creator_id=creator_id
        )
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
        self, comment_id: int, subscriber_id: int, creator_id: int | None = None
    ) -> ActionSuccessResponse:
        """
        Deletes a subscriber's own comment matching spec doc API 6.
        """
        comment = self.comment_repo.get_comment_by_id(
            comment_id, creator_id=creator_id
        )
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
