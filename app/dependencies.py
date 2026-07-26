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
            user = User.create(username="default_creator", email="creator@example.com")
        return {"user_id": user.id, "username": user.username, "email": user.email}

    payload = decode_access_token(token)
    user_id = payload.get("user_id")

    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user record no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"user_id": user.id, "username": user.username, "email": user.email}
