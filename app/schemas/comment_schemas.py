from datetime import datetime

from pydantic import BaseModel


class CommentAuthorResponse(BaseModel):
    """Canonical DTO representation of a comment author matching spec doc."""

    id: int
    name: str
    avatar_url: str | None = None
    is_creator: bool = False


class CommentReplyResponse(BaseModel):
    """DTO schema for a reply nested under a parent comment matching spec doc API 2 & API 3."""

    id: int
    comment_id: int
    text: str
    author: CommentAuthorResponse
    likes: int = 0
    is_liked: bool = False
    created_at: datetime | None = None


class CommentItemResponse(BaseModel):
    """DTO schema for top-level video comments matching spec doc API 1."""

    id: int
    text: str
    author: CommentAuthorResponse
    video_id: int
    video_title: str
    likes: int = 0
    is_liked: bool = False
    reply_count: int = 0
    created_at: datetime | None = None


class CommentReplyCreateRequest(BaseModel):
    """Request payload for posting a creator reply to a comment."""

    text: str


class CommentReplyCreateResponse(CommentReplyResponse):
    """Response payload returned when a reply is posted matching spec doc API 3."""


class CommentLikeResponse(BaseModel):
    """Response payload returned when toggling creator like state on a comment."""

    status: str = "success"
    is_liked: bool
    likes: int
