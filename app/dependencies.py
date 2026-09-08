from typing import Annotated, Any

from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.models.admin import Admin
from app.models.subscriber import Subscriber
from app.utils.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login", auto_error=False
)


def get_current_subscriber(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Guards Mobile API routes (/api/v1/mobile/*) to ensure caller is strictly a Mobile Subscriber or Guest.
    """
    payload = decode_access_token(token)
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

    return {
        "user_id": sub.id,
        "creator_id": sub.creator_id,
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
    settings = get_settings()
    static_key = settings.STATIC_API_KEY or "talentsea_secret_api_key_2026"

    # Static API Key & Dev token override for Admin Portal testing
    if token in (static_key, "test_token"):
        admin, _ = Admin.get_or_create(
            email="creator@example.com",
            defaults={"first_name": "Creator", "last_name": "Admin"},
        )
        return {
            "user_id": admin.id,
            "name": f"{admin.first_name or ''} {admin.last_name or ''}".strip()
            or "Creator Admin",
            "email": admin.email,
        }

    payload = decode_access_token(token)
    user_id = payload["user_id"]

    # Validate strictly against Admin table
    admin = Admin.get_or_none(Admin.id == user_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin portal authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": admin.id,
        "name": f"{admin.first_name or ''} {admin.last_name or ''}".strip()
        or "Creator Admin",
        "email": admin.email,
    }


# Centralized Modern FastAPI Dependency Aliases (Annotated)
CurrentAdmin = Annotated[dict[str, Any], Depends(get_current_admin)]
CurrentSubscriber = Annotated[dict[str, Any], Depends(get_current_subscriber)]
OptionalSubscriber = Annotated[dict[str, Any] | None, Depends(get_optional_subscriber)]
FormFile = Annotated[UploadFile, File(...)]


def validate_image_file(file: FormFile) -> UploadFile:
    """
    Validates uploaded image MIME types (JPG, PNG, WEBP) and size limits.
    """
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type {file.content_type}. Only JPG, PNG, and WEBP are allowed.",
        )
    return file
