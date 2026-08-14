from datetime import datetime

from pydantic import BaseModel


class MobileCommentAuthorResponse(BaseModel):
    """DTO representing the author of a comment or reply in mobile client."""

    id: int
    name: str
    avatar_url: str | None = None
    is_creator: bool = False


class MobileCommentItemResponse(BaseModel):
    """DTO representing a top-level comment item in mobile video feed matching spec doc API 1 & 2."""

    id: int
    text: str
    author: MobileCommentAuthorResponse
    likes: int = 0
    is_liked: bool = False
    reply_count: int = 0
    is_owner: bool = False
    created_at: datetime | None = None


class MobileCommentCreateRequest(BaseModel):
    """Request payload for posting a new comment or reply in mobile app."""

    text: str


class MobileCommentReplyResponse(BaseModel):
    """DTO representing a nested reply item in mobile client matching spec doc API 3 & 4."""

    id: int
    comment_id: int
    text: str
    author: MobileCommentAuthorResponse
    likes: int = 0
    is_liked: bool = False
    is_owner: bool = False
    created_at: datetime | None = None


class MobileCommentLikeResponse(BaseModel):
    """Response payload returned when toggling like on a comment in mobile client."""

    status: str = "success"
    is_liked: bool
    likes: int
