from fastapi import APIRouter, Cookie, Response, status

from app.dependencies import CurrentAdmin
from app.schemas.admin.auth_schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSummaryResponse,
    AdminTokenResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.admin.auth_service import AuthService

router = APIRouter(prefix="/api/v1/admin/auth", tags=["Admin Authentication"])
auth_service = AuthService()


@router.post("/login", response_model=AdminLoginResponse, status_code=status.HTTP_200_OK)
def admin_login(payload: AdminLoginRequest, response: Response):
    """
    POST /api/v1/admin/auth/login — Creator Admin Login with email and password.
    Returns short-lived access token and summary profile, and sets HttpOnly refresh cookie.
    """
    return auth_service.login(payload, response)


@router.post("/refresh", response_model=AdminTokenResponse, status_code=status.HTTP_200_OK)
def admin_refresh(
    response: Response,
    admin_refresh_token: str | None = Cookie(default=None),
):
    """
    POST /api/v1/admin/auth/refresh — Silent Token Refresh using HttpOnly cookie.
    Rotates refresh token and returns a newly minted access token.
    """
    return auth_service.refresh(admin_refresh_token, response)


@router.get("/me", response_model=AdminSummaryResponse, status_code=status.HTTP_200_OK)
def admin_get_me(current_admin: CurrentAdmin):
    """
    GET /api/v1/admin/auth/me — Retrieves creator session identity and studio branding for navbar/session rehydration.
    """
    return auth_service.get_me(current_admin["user_id"])


@router.post(
    "/logout",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
)
def admin_logout(current_admin: CurrentAdmin, response: Response):
    """
    POST /api/v1/admin/auth/logout — Revokes active refresh session in DB and erases HttpOnly cookie.
    """
    return auth_service.logout(current_admin["user_id"], response)
