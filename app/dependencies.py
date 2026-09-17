from typing import Annotated, Any

from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer

from app.models.admin import Admin
from app.models.subscriber import Subscriber
from app.utils.auth import decode_access_token, verify_creator_active

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login", auto_error=False
)


def get_current_subscriber(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Guards Mobile API routes (/api/v1/mobile/*) to ensure caller is strictly a Mobile Subscriber or Guest.
    """
    payload = decode_access_token(token)

    # Reject non-subscriber tokens (e.g. admin credentials) on mobile routes
    token_role = payload.get("role")
    if token_role not in ("subscriber", "guest"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Mobile subscriber credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["user_id"]

    # Validate strictly against Subscriber table
    sub = Subscriber.get_or_none(Subscriber.id == user_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated subscriber account no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not sub.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber account is disabled",
        )

    verify_creator_active(sub.creator)

    return {
        "user_id": sub.id,
        "creator_id": sub.creator_id,
        "role": sub.role,
    }


def get_optional_subscriber(
    token: str | None = Depends(oauth2_scheme_optional),
) -> dict | None:
    """
    Optional authentication for endpoints that allow guest access or guest account upgrade.
    """
    if not token:
        return None
    try:
        return get_current_subscriber(token)
    except HTTPException:
        return None


def get_current_admin(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Guards Admin Web Portal routes (/api/v1/admin/*) to ensure the caller is strictly an Admin Creator.
    Extracts admin user_id directly from token context. Subscriber tokens are rejected.
    """
    payload = decode_access_token(token)

    # Reject non-admin tokens (e.g. subscriber or guest credentials) on admin routes
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin portal authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["user_id"]

    # Validate strictly against Admin table
    admin = Admin.get_or_none(Admin.id == user_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin portal authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creator account has been deactivated. Please contact platform administration.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": admin.id,
        "name": admin.name,
        "email": admin.email,
    }


# Centralized Modern FastAPI Dependency Aliases (Annotated)
CurrentAdmin = Annotated[dict[str, Any], Depends(get_current_admin)]
CurrentSubscriber = Annotated[dict[str, Any], Depends(get_current_subscriber)]
OptionalSubscriber = Annotated[dict[str, Any] | None, Depends(get_optional_subscriber)]
FormFile = Annotated[UploadFile, File(...)]
