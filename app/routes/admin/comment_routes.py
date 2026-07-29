from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user
from app.schemas.comment_schemas import (
    CommentItemResponse,
    CommentReplyResponse,
    CommentReplyCreateRequest,
    CommentReplyCreateResponse,
    CommentLikeResponse
)
from app.schemas.common_schemas import PaginatedResponse, ActionSuccessResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api/v1/admin/comments", tags=["Admin Comments"])
comment_service = CommentService()

@router.get("", response_model=PaginatedResponse[CommentItemResponse], status_code=status.HTTP_200_OK)
def list_creator_comments(
    category: Optional[str] = Query(None, description="Filter comments by video category ID"),
    videoId: Optional[int] = Query(None, description="Filter comments by specific video ID"),
    date: Optional[str] = Query(None, description="Filter comments created on an ISO date (YYYY-MM-DD)"),
    minLikes: Optional[int] = Query(None, description="Filter comments with at least N likes"),
    search: Optional[str] = Query(None, description="Search substring within comment text"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, oldest, mostLiked"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/admin/comments — Retrieves a paginated list of top-level comments with reply_count.
    """
    return comment_service.list_creator_comments(
        creator_id=current_user["user_id"],
        search=search,
        video_id=videoId,
        category=category,
        date=date,
        min_likes=minLikes,
        sort=sort,
        page=page,
        limit=limit
    )

@router.get("/{comment_id}/replies", response_model=PaginatedResponse[CommentReplyResponse], status_code=status.HTTP_200_OK)
def get_comment_replies(
    comment_id: int,
    sort: Optional[str] = Query("oldest", description="Sort order: oldest (default), newest"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/admin/comments/{comment_id}/replies — Retrieves paginated child replies nested under a top-level comment.
    """
    return comment_service.get_comment_replies(
        creator_id=current_user["user_id"],
        comment_id=comment_id,
        sort=sort,
        page=page,
        limit=limit
    )

@router.post("/{comment_id}/reply", response_model=CommentReplyCreateResponse, status_code=status.HTTP_201_CREATED)
def post_creator_reply(
    comment_id: int,
    payload: CommentReplyCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    POST /api/v1/admin/comments/{comment_id}/reply — Posts an official creator reply to a user comment.
    """
    return comment_service.create_reply(current_user["user_id"], comment_id, payload)

@router.post("/{comment_id}/like", response_model=CommentLikeResponse, status_code=status.HTTP_200_OK)
def toggle_creator_comment_like(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    POST /api/v1/admin/comments/{comment_id}/like — Toggles creator heart/like state on a user comment.
    """
    return comment_service.toggle_comment_like(current_user["user_id"], comment_id)

@router.delete("/{comment_id}", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def delete_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    DELETE /api/v1/admin/comments/{comment_id} — Permanently deletes a comment and its replies.
    """
    return comment_service.delete_comment(current_user["user_id"], comment_id)
