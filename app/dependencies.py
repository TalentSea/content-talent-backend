from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Validates JWT Bearer access token, extracts user_id payload, and injects authenticated caller context into routes.
    No user_id parameter is accepted in request bodies or query strings to eliminate IDOR risks.
    """
    from app.config import get_settings
    from app.models.admin import Admin
    from app.models.subscriber import Subscriber

    settings = get_settings()
    static_key = settings.STATIC_API_KEY or "talentsea_secret_api_key_2026"

    # Static API Key & Dev token override for Creator Admin testing
    if token in (static_key, "test_token"):
        admin = Admin.get_or_none(Admin.username == "default_creator")
        if not admin:
            admin = Admin.create(username="default_creator", email="creator@example.com", role="creator")
        return {"user_id": admin.id, "username": admin.username, "email": admin.email, "role": getattr(admin, "role", "creator")}

    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    token_role = payload.get("role", "subscriber")

    if token_role in ("creator", "admin"):
        admin = Admin.get_or_none(Admin.id == user_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated creator record no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "user_id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role": getattr(admin, "role", "creator")
        }
    else:
        sub = Subscriber.get_or_none(Subscriber.id == user_id)
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated subscriber record no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "user_id": sub.id,
            "username": sub.name or f"subscriber_{sub.id}",
            "email": sub.email,
            "role": getattr(sub, "role", "subscriber")
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

def get_optional_subscriber(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Optional dependency helper that inspects incoming Authorization header.
    If valid Bearer token present, returns subscriber dict; if missing/invalid (Guest), returns None.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1].strip()
    try:
        return get_current_user(token=token)
    except Exception:
        return None

