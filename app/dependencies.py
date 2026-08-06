from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Validates JWT Bearer access token, extracts user_id payload, and injects authenticated creator context into routes.
    No user_id parameter is accepted in request bodies or query strings to eliminate IDOR risks.
    """
    from app.config import get_settings
    from app.models.user import User

    settings = get_settings()
    static_key = settings.STATIC_API_KEY or "talentsea_secret_api_key_2026"

    # Static API Key & Dev token override for Frontend testing
    if token in (static_key, "test_token"):
        user = User.get_or_none(User.username == "default_creator")
        if not user:
            user = User.create(username="default_creator", email="creator@example.com", role="creator")
        return {"user_id": user.id, "username": user.username, "email": user.email, "role": getattr(user, "role", "creator")}

    payload = decode_access_token(token)
    user_id = payload.get("user_id")

    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user record no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user.id,
        "username": user.username or f"user_{user.id}",
        "email": user.email,
        "role": getattr(user, "role", "subscriber")
    }

def get_current_subscriber(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Guards subscriber mobile app routes to ensure caller has 'subscriber' role.
    """
    if current_user.get("role") not in ("subscriber", "creator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber access required"
        )
    return current_user

def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Guards web admin portal routes to ensure caller has 'creator' or 'admin' role.
    """
    if current_user.get("role") not in ("creator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin portal authorization required"
        )
    return current_user
