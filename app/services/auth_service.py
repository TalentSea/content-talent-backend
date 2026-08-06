import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.config import get_settings
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth_schemas import (
    GoogleAuthRequest,
    FacebookAuthRequest,
    RefreshTokenRequest,
    AuthTokenResponse,
    UserProfileResponse
)
from app.schemas.common_schemas import ActionSuccessResponse
from app.utils.social_verifiers import verify_google_id_token, verify_facebook_access_token
from app.utils.auth import create_access_token

logger = logging.getLogger("uvicorn.error")

class AuthService:
    """
    Business logic layer for Mobile Social Authentication (Google OIDC & Facebook OAuth).
    """

    def __init__(self):
        self.repo = AuthRepository()

    def _build_user_profile_response(self, user) -> UserProfileResponse:
        """
        Maps a User Peewee instance to UserProfileResponse DTO.
        """
        name_parts = [user.first_name, user.last_name]
        full_name = " ".join([p for p in name_parts if p]).strip() or user.username

        return UserProfileResponse(
            id=user.id,
            name=full_name,
            email=user.email,
            avatar_url=user.avatar_url,
            provider=user.provider or "google",
            role=user.role or "subscriber",
            created_at=user.created_at
        )

    def _process_social_user_login(
        self,
        provider: str,
        identity_data: Dict[str, Any],
        device_info: Optional[str] = None
    ) -> AuthTokenResponse:
        """
        Common user provisioning and token issuance pipeline.
        """
        provider_id = identity_data.get("sub")
        email = identity_data.get("email")
        name = identity_data.get("name")
        avatar_url = identity_data.get("picture")

        if not provider_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Social provider {provider} did not return a valid user identity ID"
            )

        # Find existing user or create a new subscriber
        user = self.repo.find_user_by_provider_or_email(provider, provider_id, email)
        if not user:
            user = self.repo.create_social_user(
                provider=provider,
                provider_id=provider_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
                role="subscriber"
            )
        else:
            user = self.repo.update_user_profile_info(user, name, avatar_url)

        settings = get_settings()
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        # Generate App JWT Access Token and Refresh Token
        username_str = user.username or f"user_{user.id}"
        access_token = create_access_token(
            user_id=user.id,
            username=username_str,
            role=user.role or "subscriber",
            expires_delta_minutes=expire_minutes
        )
        refresh_token = self.repo.create_refresh_token_record(
            user=user,
            device_info=device_info,
            expires_in_days=expire_days
        )

        user_profile = self._build_user_profile_response(user)

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expire_minutes * 60,
            user=user_profile
        )

    def authenticate_google(self, payload: GoogleAuthRequest) -> AuthTokenResponse:
        """
        Handles dedicated Google OIDC Sign-In.
        """
        identity_data = verify_google_id_token(payload.id_token)
        return self._process_social_user_login("google", identity_data, payload.device_info)

    def authenticate_facebook(self, payload: FacebookAuthRequest) -> AuthTokenResponse:
        """
        Handles dedicated Facebook OAuth Sign-In.
        """
        identity_data = verify_facebook_access_token(payload.access_token)
        return self._process_social_user_login("facebook", identity_data, payload.device_info)

    def refresh_access_token(self, payload: RefreshTokenRequest) -> AuthTokenResponse:
        """
        Validates refresh token and issues a new access token and rotated refresh token.
        """
        token_record = self.repo.get_valid_refresh_token(payload.refresh_token)
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user = token_record.user
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account disabled or deleted"
            )

        # Revoke old refresh token (Token Rotation)
        self.repo.revoke_refresh_token(payload.refresh_token)

        settings = get_settings()
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        # Issue new token pair
        username_str = user.username or f"user_{user.id}"
        new_access_token = create_access_token(
            user_id=user.id,
            username=username_str,
            role=user.role or "subscriber",
            expires_delta_minutes=expire_minutes
        )
        new_refresh_token = self.repo.create_refresh_token_record(
            user=user,
            device_info=token_record.device_info,
            expires_in_days=expire_days
        )

        user_profile = self._build_user_profile_response(user)

        return AuthTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=expire_minutes * 60,
            user=user_profile
        )

    def logout_session(self, payload: RefreshTokenRequest) -> ActionSuccessResponse:
        """
        Revokes an active refresh token session in database.
        """
        self.repo.revoke_refresh_token(payload.refresh_token)
        return ActionSuccessResponse(status="success")

    def get_current_user_profile(self, user_id: int) -> UserProfileResponse:
        """
        Retrieves user profile metadata by user_id.
        """
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User account {user_id} not found"
            )
        return self._build_user_profile_response(user)
