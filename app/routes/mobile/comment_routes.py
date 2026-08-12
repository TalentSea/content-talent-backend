from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_subscriber, get_optional_subscriber
from app.schemas.mobile_comment_schemas import (
    MobileCommentItemResponse,
    MobileCommentCreateRequest,
    MobileCommentReplyResponse,
    MobileCommentLikeResponse
)
from app.schemas.common_schemas import PaginatedResponse, ActionSuccessResponse
from app.services.mobile_comment_service import MobileCommentService

router = APIRouter(prefix="/api/v1/mobile", tags=["Mobile Comments & Discussions"])
comment_service = MobileCommentService()

@router.get("/videos/{video_id}/comments", response_model=PaginatedResponse[MobileCommentItemResponse], status_code=status.HTTP_200_OK)
def list_video_comments(
    video_id: int,
    sort: Optional[str] = Query("newest", description="Sort order: newest, oldest, most_liked"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_subscriber: Optional[dict] = Depends(get_optional_subscriber)
):
    """
    GET /api/v1/mobile/videos/{video_id}/comments — List top-level video comments matching spec API 1.
    Accessible by guest users and authenticated subscribers.
    """
    subscriber_id = current_subscriber.get("user_id") if current_subscriber else None
    return comment_service.list_video_comments(
        video_id=video_id,
        sort=sort,
        page=page,
        limit=limit,
        subscriber_id=subscriber_id
    )

@router.post("/videos/{video_id}/comments", response_model=MobileCommentItemResponse, status_code=status.HTTP_201_CREATED)
def create_video_comment(
    video_id: int,
    payload: MobileCommentCreateRequest,
    current_subscriber: dict = Depends(get_current_subscriber)
):
    """
    POST /api/v1/mobile/videos/{video_id}/comments — Post a new top-level video comment matching spec API 2.
    Requires subscriber authentication.
    """
    subscriber_id = current_subscriber["user_id"]
    return comment_service.create_video_comment(
        video_id=video_id,
        subscriber_id=subscriber_id,
        payload=payload
    )

@router.get("/comments/{id}/replies", response_model=PaginatedResponse[MobileCommentReplyResponse], status_code=status.HTTP_200_OK)
def get_comment_replies(
    id: int,
    sort: Optional[str] = Query("oldest", description="Sort order: oldest, newest"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_subscriber: Optional[dict] = Depends(get_optional_subscriber)
):
    """
    GET /api/v1/mobile/comments/{id}/replies — Fetch thread child replies matching spec API 3.
    Accessible by guest users and authenticated subscribers.
    """
    subscriber_id = current_subscriber.get("user_id") if current_subscriber else None
    return comment_service.get_comment_replies(
        comment_id=id,
        sort=sort,
        page=page,
        limit=limit,
        subscriber_id=subscriber_id
    )

@router.post("/comments/{id}/replies", response_model=MobileCommentReplyResponse, status_code=status.HTTP_201_CREATED)
def create_comment_reply(
    id: int,
    payload: MobileCommentCreateRequest,
    current_subscriber: dict = Depends(get_current_subscriber)
):
    """
    POST /api/v1/mobile/comments/{id}/replies — Post reply to a comment or sub-comment matching spec API 4.
    Requires subscriber authentication.
    """
    subscriber_id = current_subscriber["user_id"]
    return comment_service.create_comment_reply(
        comment_id=id,
        subscriber_id=subscriber_id,
        payload=payload
    )

@router.post("/comments/{id}/like", response_model=MobileCommentLikeResponse, status_code=status.HTTP_200_OK)
def toggle_comment_like(
    id: int,
    current_subscriber: dict = Depends(get_current_subscriber)
):
    """
    POST /api/v1/mobile/comments/{id}/like — Toggle subscriber like state on a comment matching spec API 5.
    Requires subscriber authentication.
    """
    subscriber_id = current_subscriber["user_id"]
    return comment_service.toggle_comment_like(
        comment_id=id,
        subscriber_id=subscriber_id
    )

@router.delete("/comments/{id}", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def delete_comment(
    id: int,
    current_subscriber: dict = Depends(get_current_subscriber)
):
    """
    DELETE /api/v1/mobile/comments/{id} — Delete subscriber's own comment matching spec API 6.
    Requires subscriber authentication.
    """
    subscriber_id = current_subscriber["user_id"]
    return comment_service.delete_comment(
        comment_id=id,
        subscriber_id=subscriber_id
    )
