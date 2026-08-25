import logging
from typing import Any

from fastapi import HTTPException, status

from app.config import get_settings
from app.models.subscriber import Subscriber
from app.repositories.mobile.auth_repository import AuthRepository
from app.schemas.mobile.auth_schemas import (
    AuthTokenResponse,
    FacebookAuthRequest,
    GoogleAuthRequest,
    GuestAuthRequest,
    RefreshTokenRequest,
    UserProfileResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.utils.auth import create_access_token
from app.utils.idp_verifiers import (
    verify_facebook_access_token,
    verify_google_id_token,
)

logger = logging.getLogger("uvicorn.error")


class AuthService:
    """
    Business logic layer for Mobile Social Authentication (Google OIDC, Facebook OAuth, Guest Sessions).
    """

    def __init__(self):
        self.repo = AuthRepository()

    def _build_user_profile_response(
        self, subscriber: Subscriber
    ) -> UserProfileResponse:
        """
        Maps a Subscriber Peewee ORM instance to UserProfileResponse DTO.
        """
        return UserProfileResponse(
            id=subscriber.id,
            name=subscriber.name or f"Subscriber {subscriber.id}",
            email=subscriber.email,
            avatar_url=subscriber.avatar_url,
            provider=subscriber.provider or "google",
            role="subscriber" if subscriber.provider != "guest" else "guest",
            created_at=subscriber.created_at,
        )

    def _process_social_user_login(
        self,
        creator_id: int,
        provider: str,
        identity_data: dict[str, Any],
        device_info: str | None = None,
        guest_subscriber_id: int | None = None,
    ) -> AuthTokenResponse:
        """
        Common subscriber provisioning, account upgrade, and token issuance pipeline bound to creator_id.
        """
        provider_id = identity_data.get("sub")
        email = identity_data.get("email")
        name = identity_data.get("name")
        avatar_url = identity_data.get("picture")

        if not provider_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Social provider {provider} did not return a valid user identity ID",
            )

        # 1. If active guest_subscriber_id is provided, upgrade the existing Guest account in-place!
        subscriber = None
        if guest_subscriber_id:
            guest_sub = self.repo.get_user_by_id(guest_subscriber_id)
            if guest_sub and guest_sub.provider == "guest":
                subscriber = self.repo.upgrade_guest_subscriber(
                    guest_subscriber_id=guest_subscriber_id,
                    creator_id=creator_id,
                    provider=provider,
                    provider_id=provider_id,
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                )

        # 2. Otherwise find existing subscriber or create a new subscriber record bound to creator_id
        if not subscriber:
            subscriber = self.repo.find_user_by_provider_or_email(
                creator_id, provider, provider_id, email
            )
            if not subscriber:
                subscriber = self.repo.create_social_user(
                    creator_id=creator_id,
                    provider=provider,
                    provider_id=provider_id,
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                )
            else:
                subscriber = self.repo.update_user_profile_info(
                    subscriber, name, avatar_url
                )

        settings = get_settings()
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        # Generate App JWT Access Token containing user_id and creator_id
        username_str = subscriber.name or f"subscriber_{subscriber.id}"
        access_token = create_access_token(
            user_id=subscriber.id,
            username=username_str,
            creator_id=subscriber.creator_id,
            expires_delta_minutes=expire_minutes,
        )
        refresh_token = self.repo.create_refresh_token_record(
            subscriber=subscriber, device_info=device_info, expires_in_days=expire_days
        )

        user_profile = self._build_user_profile_response(subscriber)

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expire_minutes * 60,
            user=user_profile,
        )

    def authenticate_guest(self, payload: GuestAuthRequest) -> AuthTokenResponse:
        """
        Handles Anonymous Guest Session ("Skip Signup") authentication bound to creator_id.
        """
        subscriber = self.repo.get_or_create_guest_subscriber(
            creator_id=payload.creator_id, device_id=payload.device_id
        )

        settings = get_settings()
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        access_token = create_access_token(
            user_id=subscriber.id,
            username=subscriber.name or f"guest_{subscriber.id}",
            creator_id=subscriber.creator_id,
            expires_delta_minutes=expire_minutes,
        )
        refresh_token = self.repo.create_refresh_token_record(
            subscriber=subscriber,
            device_info=payload.device_info,
            expires_in_days=expire_days,
        )

        user_profile = self._build_user_profile_response(subscriber)

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expire_minutes * 60,
            user=user_profile,
        )

    def authenticate_google(
        self, payload: GoogleAuthRequest, guest_subscriber_id: int | None = None
    ) -> AuthTokenResponse:
        """
        Handles dedicated Google OIDC Sign-In and optional Guest Account Upgrade.
        """
        identity_data = verify_google_id_token(payload.id_token)
        return self._process_social_user_login(
            creator_id=payload.creator_id,
            provider="google",
            identity_data=identity_data,
            device_info=payload.device_info,
            guest_subscriber_id=guest_subscriber_id,
        )

    def authenticate_facebook(
        self, payload: FacebookAuthRequest, guest_subscriber_id: int | None = None
    ) -> AuthTokenResponse:
        """
        Handles dedicated Facebook OAuth Sign-In and optional Guest Account Upgrade.
        """
        identity_data = verify_facebook_access_token(payload.access_token)
        return self._process_social_user_login(
            creator_id=payload.creator_id,
            provider="facebook",
            identity_data=identity_data,
            device_info=payload.device_info,
            guest_subscriber_id=guest_subscriber_id,
        )

    def refresh_access_token(self, payload: RefreshTokenRequest) -> AuthTokenResponse:
        """
        Validates refresh token and issues a new access token and rotated refresh token.
        """
        token_record = self.repo.get_valid_refresh_token(payload.refresh_token)
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        subscriber = token_record.user
        if not subscriber or not subscriber.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Subscriber account is disabled",
            )

        # Revoke old refresh token (Token Rotation)
        self.repo.revoke_refresh_token(payload.refresh_token)

        settings = get_settings()
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        # Issue new token pair
        username_str = subscriber.name or f"subscriber_{subscriber.id}"
        new_access_token = create_access_token(
            user_id=subscriber.id,
            username=username_str,
            creator_id=subscriber.creator_id,
            expires_delta_minutes=expire_minutes,
        )
        new_refresh_token = self.repo.create_refresh_token_record(
            subscriber=subscriber,
            device_info=token_record.device_info,
            expires_in_days=expire_days,
        )

        user_profile = self._build_user_profile_response(subscriber)

        return AuthTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=expire_minutes * 60,
            user=user_profile,
        )

    def logout_session(self, payload: RefreshTokenRequest) -> ActionSuccessResponse:
        """
        Revokes an active refresh token session in database.
        """
        self.repo.revoke_refresh_token(payload.refresh_token)
        return ActionSuccessResponse(status="success")

    def get_current_user_profile(self, user_id: int) -> UserProfileResponse:
        """
        Retrieves subscriber profile metadata by user_id.
        """
        subscriber = self.repo.get_user_by_id(user_id)
        if not subscriber or not subscriber.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscriber account {user_id} not found",
            )
        return self._build_user_profile_response(subscriber)
