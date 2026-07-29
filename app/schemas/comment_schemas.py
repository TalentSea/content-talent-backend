from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class CommentReplyResponse(BaseModel):
    """DTO schema for a reply nested under a parent comment."""
    id: int
    comment_id: int
    text: str
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    created_at: Optional[datetime] = None

class CommentItemResponse(BaseModel):
    """DTO schema for top-level video comments matching spec doc."""
    id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    text: str
    video_id: int
    video_title: str
    likes: int = 0
    is_liked: bool = False
    reply_count: int = 0
    created_at: Optional[datetime] = None

class CommentReplyCreateRequest(BaseModel):
    """Request payload for posting a creator reply to a comment."""
    text: str

class CommentReplyCreateResponse(BaseModel):
    """Response payload returned when a reply is posted matching spec doc."""
    id: int
    comment_id: int
    text: str
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    created_at: Optional[datetime] = None

class CommentLikeResponse(BaseModel):
    """Response payload returned when toggling creator like state on a comment."""
    status: str = "success"
    is_liked: bool
    likes: int
