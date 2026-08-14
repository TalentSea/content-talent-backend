from fastapi import APIRouter, Query, status

from app.dependencies import CurrentAdmin
from app.schemas.comment_schemas import (
    CommentItemResponse,
    CommentLikeResponse,
    CommentReplyCreateRequest,
    CommentReplyCreateResponse,
    CommentReplyResponse,
)
from app.schemas.common_schemas import ActionSuccessResponse, PaginatedResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api/v1/admin/comments", tags=["Admin Comments"])
comment_service = CommentService()


@router.get(
    "",
    response_model=PaginatedResponse[CommentItemResponse],
    status_code=status.HTTP_200_OK,
)
def list_creator_comments(
    current_user: CurrentAdmin,
    category: str | None = Query(
        None, description="Filter comments by video category ID"
    ),
    videoId: int | None = Query(
        None, description="Filter comments by specific video ID"
    ),
    date: str | None = Query(
        None, description="Filter comments created on an ISO date (YYYY-MM-DD)"
    ),
    minLikes: int | None = Query(
        None, description="Filter comments with at least N likes"
    ),
    search: str | None = Query(
        None, description="Search substring within comment text"
    ),
    sort: str | None = Query(
        "newest", description="Sort order: newest, oldest, mostLiked"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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
        limit=limit,
    )


@router.post(
    "/videos/{video_id}/comments",
    response_model=CommentItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_creator_top_level_comment(
    video_id: int, payload: CommentReplyCreateRequest, current_user: CurrentAdmin
):
    """
    POST /api/v1/admin/videos/{video_id}/comments — Posts an official creator top-level comment matching spec API 2.
    """
    return comment_service.create_top_level_comment(
        creator_id=current_user["user_id"], video_id=video_id, payload=payload
    )


@router.get(
    "/{comment_id}/replies",
    response_model=PaginatedResponse[CommentReplyResponse],
    status_code=status.HTTP_200_OK,
)
def get_comment_replies(
    comment_id: int,
    current_user: CurrentAdmin,
    sort: str | None = Query(
        "oldest", description="Sort order: oldest (default), newest"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    GET /api/v1/admin/comments/{comment_id}/replies — Retrieves paginated child replies nested under a top-level comment.
    """
    return comment_service.get_comment_replies(
        creator_id=current_user["user_id"],
        comment_id=comment_id,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.post(
    "/{comment_id}/reply",
    response_model=CommentReplyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_creator_reply(
    comment_id: int, payload: CommentReplyCreateRequest, current_user: CurrentAdmin
):
    """
    POST /api/v1/admin/comments/{comment_id}/reply — Posts an official creator reply to a user comment.
    """
    return comment_service.create_reply(current_user["user_id"], comment_id, payload)


@router.post(
    "/{comment_id}/like",
    response_model=CommentLikeResponse,
    status_code=status.HTTP_200_OK,
)
def toggle_creator_comment_like(comment_id: int, current_user: CurrentAdmin):
    """
    POST /api/v1/admin/comments/{comment_id}/like — Toggles creator heart/like state on a user comment.
    """
    return comment_service.toggle_comment_like(current_user["user_id"], comment_id)


@router.delete(
    "/{comment_id}",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def delete_comment(comment_id: int, current_user: CurrentAdmin):
    """
    DELETE /api/v1/admin/comments/{comment_id} — Permanently deletes a comment and its replies.
    """
    return comment_service.delete_comment(current_user["user_id"], comment_id)
