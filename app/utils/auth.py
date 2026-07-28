from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from app.config import get_settings

def create_access_token(user_id: int, username: str, expires_delta_minutes: int = 60) -> str:
    """
    Encodes user_id and username into a signed JWT access token.
    """
    settings = get_settings()
    secret_key = settings.JWT_SECRET_KEY or "dev_secret_key_change_in_production"
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    
    to_encode = {
        "sub": str(user_id),
        "user_id": user_id,
        "username": username,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Decodes JWT Bearer token and returns claims payload dictionary.
    Raises HTTPException(401) if token is expired or invalid.
    """
    settings = get_settings()
    secret_key = settings.JWT_SECRET_KEY or "dev_secret_key_change_in_production"
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

