from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from app.config import get_settings

def create_access_token(user_id: int, username: str, expires_delta_minutes: int = 60) -> str:
    """
    Encodes user_id and username into a signed JWT access token.
    """
    pass

def decode_access_token(token: str) -> dict:
    """
    Decodes JWT Bearer token and returns claims payload dictionary.
    Raises HTTPException(401) if token is expired or invalid.
    """
    pass
