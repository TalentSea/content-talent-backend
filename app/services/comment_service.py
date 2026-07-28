import logging
import math
from typing import Optional, List
from fastapi import HTTPException, status

from app.repositories.comment_repository import CommentRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.comment_schemas import (
    CommentItemResponse,
    CommentReplyResponse,
    CommentReplyCreateRequest,
    CommentReplyCreateResponse,
    CommentLikeResponse
)
from app.schemas.common_schemas import PaginatedResponse, ActionSuccessResponse

logger = logging.getLogger(__name__)

class CommentService:
    """
    Business logic layer for Admin Comment & Moderation operations.
    """

    def __init__(self):
        self.comment_repo = CommentRepository()
        self.profile_repo = ProfileRepository()

    def list_creator_comments(
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
    ) -> PaginatedResponse[CommentItemResponse]:
        """
        Retrieves paginated top-level comments with reply_count matching spec doc API 1.
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
            limit=limit
        )

        items: List[CommentItemResponse] = []
        for c in comments:
            reply_count = self.comment_repo.get_reply_count_for_comment(c.id)
            is_liked = self.comment_repo.is_comment_liked_by_user(c.id, creator_id)

            item = CommentItemResponse(
                id=c.id,
                user_id=c.user.id,
                user_name=c.user_name,
                user_avatar=c.user_avatar,
                text=c.text,
                video_id=c.video.id,
                video_title=c.video.title,
                likes=c.likes,
                is_liked=is_liked,
                reply_count=reply_count,
                created_at=c.created_at
            )
            items.append(item)

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items
        )

    def get_comment_replies(
        self,
        creator_id: int,
        comment_id: int,
        sort: Optional[str] = "oldest",
        page: int = 1,
        limit: int = 20
    ) -> PaginatedResponse[CommentReplyResponse]:
        """
        Retrieves paginated child replies nested under a parent comment matching spec doc API 2.
        """
        parent_comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not parent_comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment {comment_id} not found")

        replies_raw, total = self.comment_repo.get_replies_for_comment(
            comment_id=comment_id,
            sort=sort,
            page=page,
            limit=limit
        )

        items = [
            CommentReplyResponse(
                id=r.id,
                comment_id=parent_comment.id,
                text=r.text,
                user_id=r.user.id,
                user_name=r.user_name,
                user_avatar=r.user_avatar,
                created_at=r.created_at
            )
            for r in replies_raw
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items
        )

    def create_reply(self, creator_id: int, comment_id: int, payload: CommentReplyCreateRequest) -> CommentReplyCreateResponse:
        """
        Posts an official creator reply to a user comment matching spec doc API 3.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment {comment_id} not found")

        creator_user = self.profile_repo.get_profile_by_user_id(creator_id)
        if not creator_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator account not found")

        reply = self.comment_repo.create_reply(comment, creator_user, payload.text)

        return CommentReplyCreateResponse(
            id=reply.id,
            comment_id=reply.parent.id,  # Guarantees root parent ID is returned
            text=reply.text,
            user_id=creator_user.id,
            user_name=reply.user_name,
            user_avatar=reply.user_avatar,
            created_at=reply.created_at
        )

    def toggle_comment_like(self, creator_id: int, comment_id: int) -> CommentLikeResponse:
        """
        Toggles creator like state in comment_likes table matching spec doc API 4.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment {comment_id} not found")

        is_liked, likes = self.comment_repo.toggle_like(comment, creator_id)

        return CommentLikeResponse(
            status="success",
            is_liked=is_liked,
            likes=likes
        )

    def delete_comment(self, creator_id: int, comment_id: int) -> ActionSuccessResponse:
        """
        Deletes a comment permanently matching spec doc API 5.
        """
        comment = self.comment_repo.get_comment_by_id(comment_id, creator_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment {comment_id} not found")

        self.comment_repo.delete_comment(comment)

        return ActionSuccessResponse(status="success")
