import logging

from fastapi import HTTPException, Response, status

from app.config import get_settings
from app.repositories.admin.auth_repository import AuthRepository
from app.schemas.admin.auth_schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSummaryResponse,
    AdminTokenResponse,
)
from app.utils.auth import (
    create_access_token,
    create_refresh_token_string,
    hash_refresh_token,
    verify_password,
    verify_tenant_active,
)
from app.utils.string_utils import format_full_name

logger = logging.getLogger(__name__)


class AuthService:
    """
    Business logic layer for Creator Admin Authentication, token lifecycle, and session management.
    Supports both Tenant Admins and Platform Super Admins.
    """

    REFRESH_COOKIE_NAME = "admin_refresh_token"
    REFRESH_COOKIE_PATH = "/api/v1/admin/auth"
    ACCESS_COOKIE_NAME = "admin_access_token"
    ACCESS_COOKIE_PATH = "/api/v1/admin"

    def __init__(self, repo: AuthRepository | None = None):
        self.repo = repo or AuthRepository()

    # --- Private Reusable Helpers ---

    def _set_access_cookie(self, response: Response, raw_token: str) -> None:
        """
        Sets a cryptographically secure HttpOnly cookie for the creator admin access token.
        """
        settings = get_settings()
        response.set_cookie(
            key=self.ACCESS_COOKIE_NAME,
            value=raw_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=True,
            samesite="none",
            path=self.ACCESS_COOKIE_PATH,
        )

    def _clear_access_cookie(self, response: Response) -> None:
        """
        Invalidates and erases the HttpOnly access token cookie in the client browser.
        """
        response.delete_cookie(
            key=self.ACCESS_COOKIE_NAME,
            path=self.ACCESS_COOKIE_PATH,
            httponly=True,
            secure=True,
            samesite="none",
        )

    def _set_refresh_cookie(self, response: Response, raw_token: str) -> None:
        """
        Sets a cryptographically secure HttpOnly cookie for the creator admin refresh token.
        """
        settings = get_settings()
        response.set_cookie(
            key=self.REFRESH_COOKIE_NAME,
            value=raw_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            httponly=True,
            secure=True,
            samesite="none",
            path=self.REFRESH_COOKIE_PATH,
        )

    def _clear_refresh_cookie(self, response: Response) -> None:
        """
        Invalidates and erases the HttpOnly refresh cookie in the client browser.
        """
        response.delete_cookie(
            key=self.REFRESH_COOKIE_NAME,
            path=self.REFRESH_COOKIE_PATH,
            httponly=True,
            secure=True,
            samesite="none",
        )

    def _create_admin_access_token(
        self,
        admin_id: int,
        first_name: str | None,
        last_name: str | None,
        role: str = "admin",
        tenant_id: int | None = None,
    ) -> str:
        """
        Encodes admin identity into a signed JWT access token with role and tenant_id.
        """
        settings = get_settings()
        return create_access_token(
            user_id=admin_id,
            role=role,
            username=format_full_name(first_name, last_name),
            tenant_id=tenant_id,
            expires_delta_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    def _rotate_refresh_session(self, admin_id: int, response: Response) -> None:
        """
        Generates a new refresh token, saves its SHA-256 hash in DB, and sets the secure HttpOnly cookie.
        """
        raw_refresh_token = create_refresh_token_string()
        token_hash = hash_refresh_token(raw_refresh_token)
        self.repo.update_refresh_token_hash(admin_id, token_hash)
        self._set_refresh_cookie(response, raw_refresh_token)

    # --- Public Authentication Endpoints ---

    def login(
        self, credentials: AdminLoginRequest, response: Response
    ) -> AdminLoginResponse:
        """
        Authenticates an admin or super admin with email/password and sets a secure HttpOnly refresh cookie.
        """
        admin = self.repo.get_admin_by_email(credentials.email)
        if (
            not admin
            or not admin.password_hash
            or not verify_password(credentials.password, admin.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not getattr(admin, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account has been deactivated. Please contact platform administration.",
            )

        is_super_admin = admin.role == "super_admin"
        tenant_id = None
        if not is_super_admin:
            if not admin.tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin account is not assigned to any studio tenant.",
                )
            verify_tenant_active(admin.tenant)
            tenant_id = admin.tenant_id
            studio_name = admin.tenant.name
            avatar_url = admin.avatar_url
            is_owner = admin.is_owner
        else:
            tenant_id = None
            studio_name = None
            avatar_url = None
            is_owner = False

        settings = get_settings()

        # Issue access token & provision cookies
        access_token = self._create_admin_access_token(
            admin_id=admin.id,
            first_name=admin.first_name,
            last_name=admin.last_name,
            role=admin.role,
            tenant_id=tenant_id,
        )
        self._set_access_cookie(response, access_token)
        self._rotate_refresh_session(admin.id, response)

        return AdminLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            admin=AdminSummaryResponse(
                id=admin.id,
                email=admin.email,
                first_name=admin.first_name,
                last_name=admin.last_name,
                studio_name=studio_name,
                avatar_url=avatar_url,
                role=admin.role,
                tenant_id=tenant_id,
                is_owner=is_owner,
            ),
        )

    def refresh(
        self, cookie_token: str | None, response: Response
    ) -> AdminTokenResponse:
        """
        Silently renews an access token and rotates the refresh token using the incoming HttpOnly cookie.
        """
        if not cookie_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing",
            )

        incoming_hash = hash_refresh_token(cookie_token)
        admin = self.repo.get_admin_by_refresh_token_hash(incoming_hash)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or active on another device; please re-login",
            )

        if not getattr(admin, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account has been deactivated. Please contact platform administration.",
            )

        tenant_id = None
        if admin.role != "super_admin":
            if not admin.tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin account is not assigned to any studio tenant.",
                )
            verify_tenant_active(admin.tenant)
            tenant_id = admin.tenant_id

        settings = get_settings()

        # Rotate single-use refresh session & issue fresh access token
        self._rotate_refresh_session(admin.id, response)
        new_access_token = self._create_admin_access_token(
            admin_id=admin.id,
            first_name=admin.first_name,
            last_name=admin.last_name,
            role=admin.role,
            tenant_id=tenant_id,
        )
        self._set_access_cookie(response, new_access_token)

        return AdminTokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def get_me(self, admin_id: int) -> AdminSummaryResponse:
        """
        Rehydrates admin identity and studio tenant info for SPA navbar and session initialization.
        """
        admin = self.repo.get_admin_by_id(admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin account not found",
            )

        is_super_admin = admin.role == "super_admin"
        tenant_id = admin.tenant_id if not is_super_admin else None
        studio_name = admin.tenant.name if (not is_super_admin and admin.tenant) else None
        avatar_url = admin.avatar_url if not is_super_admin else None
        is_owner = admin.is_owner if not is_super_admin else False

        return AdminSummaryResponse(
            id=admin.id,
            email=admin.email,
            first_name=admin.first_name,
            last_name=admin.last_name,
            studio_name=studio_name,
            avatar_url=avatar_url,
            role=admin.role,
            tenant_id=tenant_id,
            is_owner=is_owner,
        )

    def logout(self, admin_id: int, response: Response) -> dict[str, str]:
        """
        Revokes creator refresh session in database and clears the browser HttpOnly cookies.
        """
        self.repo.update_refresh_token_hash(admin_id, None)
        self._clear_refresh_cookie(response)
        self._clear_access_cookie(response)
        return {"message": "Successfully logged out"}
