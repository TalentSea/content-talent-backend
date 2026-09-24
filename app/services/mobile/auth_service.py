import json
import logging
import secrets
from typing import Any

from fastapi import HTTPException, status

from app.config import get_settings
from app.models.subscriber import Subscriber
from app.repositories.mobile.auth_repository import AuthRepository
from app.repositories.mobile.verification_repository import VerificationRepository
from app.schemas.mobile.auth_schemas import (
    AuthTokenResponse,
    FacebookAuthRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    GuestAuthRequest,
    MobileLoginRequest,
    MobileRegisterRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    UserProfileResponse,
    VerifyRegistrationRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.shared.email_service import EmailService
from app.utils.auth import (
    create_access_token,
    create_reset_token,
    decode_reset_token,
    hash_password,
    verify_password,
    verify_tenant_active,
    verify_verification_code,
)
from app.utils.idp_verifiers import (
    verify_facebook_access_token,
    verify_google_id_token,
)

logger = logging.getLogger("uvicorn.error")


class AuthService:
    """
    Business logic layer for Mobile Subscriber Authentication:
    - Native Email & Password Registration & Verification (6-digit In-App OTP)
    - Native Email & Password Login
    - 2-Step In-App Password Reset with Stateless Signed JWT Reset Token
    - Google OIDC & Facebook OAuth Sign-In with Smart Account Linking
    - Anonymous Hardware-Bound Guest Sessions
    """

    def __init__(self):
        self.repo = AuthRepository()
        self.verification_repo = VerificationRepository()
        self.email_service = EmailService()

    def _build_user_profile_response(
        self, subscriber: Subscriber
    ) -> UserProfileResponse:
        """
        Maps a Subscriber Peewee ORM instance to UserProfileResponse DTO.
        """
        return UserProfileResponse(
            id=subscriber.id,
            name=subscriber.name,
            email=subscriber.email,
            avatar_url=subscriber.avatar_url,
            provider=subscriber.provider,
            role="subscriber" if subscriber.provider != "guest" else "guest",
            created_at=subscriber.created_at,
        )

    def _issue_auth_session(
        self, subscriber: Subscriber, device_info: str | None = None
    ) -> AuthTokenResponse:
        """
        Common token issuance pipeline: creates App JWT Access Token and DB Refresh Token.
        """
        settings = get_settings()
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        role_str = subscriber.role or ("subscriber" if subscriber.provider != "guest" else "guest")
        access_token = create_access_token(
            user_id=subscriber.id,
            role=role_str,
            username=subscriber.name or "",
            tenant_id=subscriber.tenant_id,
            expires_delta_minutes=expire_minutes,
        )
        refresh_token = self.repo.create_refresh_token_record(
            subscriber=subscriber,
            device_info=device_info,
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

    # --------------------------------------------------------------------------
    # Native Mobile Email & Password Flows
    # --------------------------------------------------------------------------

    def initiate_registration(
        self, payload: MobileRegisterRequest
    ) -> ActionSuccessResponse:
        """
        Initiates email registration: validates conflicts, enforces cooldown,
        temporarily stores hashed code & payload in VerificationCode, and sends OTP.
        """
        verify_tenant_active(payload.tenant_id)
        email = payload.email.lower().strip()

        # Check if email is already registered with a password
        existing_user = self.repo.find_user_by_email(payload.tenant_id, email)
        if existing_user and existing_user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered. Please log in.",
            )

        # Enforce 60-second resend cooldown
        settings = get_settings()
        cooldown_sec = getattr(settings, "VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS", 60)
        recent = self.verification_repo.get_recent_code(
            tenant_id=payload.tenant_id,
            email=email,
            purpose="registration",
            within_seconds=cooldown_sec,
        )
        if recent:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait 60 seconds before requesting another code.",
            )

        # Generate cryptographically secure 6-digit OTP
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        password_hash = hash_password(payload.password)

        self.verification_repo.store_registration_otp(
            tenant_id=payload.tenant_id,
            email=email,
            raw_code=code,
            name=payload.name,
            password_hash=password_hash,
        )

        is_linked = bool(existing_user is not None)
        self.email_service.send_registration_otp(
            email=email, code=code, is_linked_account=is_linked
        )

        return ActionSuccessResponse(status="success")

    def verify_registration(
        self, payload: VerifyRegistrationRequest
    ) -> AuthTokenResponse:
        """
        Submits 6-digit OTP: verifies code, creates or smart-links subscriber,
        immediately deletes OTP record, and issues auth session tokens.
        """
        verify_tenant_active(payload.tenant_id)
        email = payload.email.lower().strip()

        code_record = self.verification_repo.get_latest_code_for_email(
            tenant_id=payload.tenant_id, email=email, purpose="registration"
        )
        if not code_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code.",
            )

        settings = get_settings()
        max_attempts = getattr(settings, "VERIFICATION_CODE_MAX_ATTEMPTS", 5)

        if code_record.attempts >= max_attempts:
            self.verification_repo.delete_code(code_record.id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new code.",
            )

        if not verify_verification_code(payload.code, code_record.code_hash):
            attempts = self.verification_repo.increment_attempts(code_record)
            if attempts >= max_attempts:
                self.verification_repo.delete_code(code_record.id)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Please request a new code.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code.",
            )

        # Code is valid; extract registration payload
        data = json.loads(code_record.payload_data) if code_record.payload_data else {}
        name = data.get("name") or "Subscriber"
        password_hash = data.get("password_hash")

        # Smart linking: if subscriber already exists via Google, link password and update name
        subscriber = self.repo.find_user_by_email(payload.tenant_id, email)
        if subscriber:
            subscriber = self.repo.link_password_and_update_name(
                subscriber=subscriber,
                name=name,
                password_hash=password_hash,
            )
        else:
            subscriber = self.repo.create_local_user(
                tenant_id=payload.tenant_id,
                name=name,
                email=email,
                password_hash=password_hash,
            )

        # Immediately purge the OTP verification record
        self.verification_repo.delete_code(code_record.id)

        return self._issue_auth_session(subscriber, device_info=payload.device_info)

    def login_local_subscriber(
        self, payload: MobileLoginRequest
    ) -> AuthTokenResponse:
        """
        Authenticates registered subscribers using email address and password.
        """
        verify_tenant_active(payload.tenant_id)
        email = payload.email.lower().strip()

        subscriber = self.repo.find_user_by_email(payload.tenant_id, email)
        if not subscriber or not subscriber.password_hash or not verify_password(payload.password, subscriber.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not subscriber.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support.",
            )

        return self._issue_auth_session(subscriber, device_info=payload.device_info)

    def request_password_reset(
        self, payload: ForgotPasswordRequest
    ) -> ActionSuccessResponse:
        """
        Dispatches a 6-digit password reset OTP code. Always returns success to prevent user enumeration.
        """
        verify_tenant_active(payload.tenant_id)
        email = payload.email.lower().strip()

        subscriber = self.repo.find_user_by_email(payload.tenant_id, email)
        if subscriber and subscriber.is_active:
            settings = get_settings()
            cooldown_sec = getattr(settings, "VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS", 60)
            recent = self.verification_repo.get_recent_code(
                tenant_id=payload.tenant_id,
                email=email,
                purpose="password_reset",
                within_seconds=cooldown_sec,
            )
            if not recent:
                code = f"{secrets.randbelow(900000) + 100000:06d}"
                self.verification_repo.store_password_reset_otp(
                    tenant_id=payload.tenant_id,
                    email=email,
                    raw_code=code,
                )
                has_google = bool(subscriber.provider == "google")
                self.email_service.send_password_reset_otp(
                    email=email,
                    code=code,
                    has_google_linked=has_google,
                )

        return ActionSuccessResponse(status="success")

    def verify_reset_code(
        self, payload: VerifyResetCodeRequest
    ) -> VerifyResetCodeResponse:
        """
        Validates 6-digit reset OTP, deletes the OTP record immediately,
        and returns a 10-minute stateless signed JWT reset_token.
        """
        verify_tenant_active(payload.tenant_id)
        email = payload.email.lower().strip()

        code_record = self.verification_repo.get_latest_code_for_email(
            tenant_id=payload.tenant_id, email=email, purpose="password_reset"
        )
        if not code_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code.",
            )

        settings = get_settings()
        max_attempts = getattr(settings, "VERIFICATION_CODE_MAX_ATTEMPTS", 5)

        if code_record.attempts >= max_attempts:
            self.verification_repo.delete_code(code_record.id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new code.",
            )

        if not verify_verification_code(payload.code, code_record.code_hash):
            attempts = self.verification_repo.increment_attempts(code_record)
            if attempts >= max_attempts:
                self.verification_repo.delete_code(code_record.id)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Please request a new code.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code.",
            )

        # Code valid: immediately delete OTP row
        self.verification_repo.delete_code(code_record.id)

        # Issue 10-minute stateless signed JWT reset token
        reset_token = create_reset_token(
            email=email,
            tenant_id=payload.tenant_id,
            expires_minutes=getattr(settings, "VERIFICATION_CODE_EXPIRE_MINUTES", 10),
        )

        return VerifyResetCodeResponse(status="success", reset_token=reset_token)

    def reset_password_with_token(
        self, payload: ResetPasswordRequest
    ) -> AuthTokenResponse:
        """
        Validates cryptographically signed reset_token, sets new password,
        and returns fresh session JWT tokens for instant auto-login.
        """
        claims = decode_reset_token(payload.reset_token)
        email = claims["email"]
        tenant_id = claims["tenant_id"]

        verify_tenant_active(tenant_id)

        subscriber = self.repo.find_user_by_email(tenant_id, email)
        if not subscriber:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscriber account not found.",
            )

        if not subscriber.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support.",
            )

        new_password_hash = hash_password(payload.new_password)
        subscriber = self.repo.update_user_password(subscriber, new_password_hash)

        return self._issue_auth_session(subscriber)

    # --------------------------------------------------------------------------
    # Social & Guest Authentication Flows
    # --------------------------------------------------------------------------

    def _process_social_user_login(
        self,
        tenant_id: int,
        provider: str,
        identity_data: dict[str, Any],
        device_info: str | None = None,
    ) -> AuthTokenResponse:
        """
        Common social subscriber provisioning and token issuance pipeline bound to tenant_id.
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

        verify_tenant_active(tenant_id)

        # Find existing subscriber or create a new subscriber record bound to tenant_id
        subscriber = self.repo.find_user_by_provider_or_email(
            tenant_id, provider, provider_id, email
        )
        if not subscriber:
            subscriber = self.repo.create_social_user(
                tenant_id=tenant_id,
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

        return self._issue_auth_session(subscriber, device_info=device_info)

    def authenticate_guest(self, payload: GuestAuthRequest) -> AuthTokenResponse:
        """
        Handles Anonymous Guest Session ("Skip Signup") authentication bound to tenant_id.
        """
        verify_tenant_active(payload.tenant_id)

        subscriber = self.repo.get_or_create_guest_subscriber(
            tenant_id=payload.tenant_id, device_id=payload.device_id
        )

        return self._issue_auth_session(subscriber, device_info=payload.device_info)

    def authenticate_google(
        self, payload: GoogleAuthRequest
    ) -> AuthTokenResponse:
        """
        Handles dedicated Google OIDC Sign-In.
        """
        identity_data = verify_google_id_token(payload.id_token)
        return self._process_social_user_login(
            tenant_id=payload.tenant_id,
            provider="google",
            identity_data=identity_data,
            device_info=payload.device_info,
        )

    def authenticate_facebook(
        self, payload: FacebookAuthRequest
    ) -> AuthTokenResponse:
        """
        Handles dedicated Facebook OAuth Sign-In.
        """
        identity_data = verify_facebook_access_token(payload.access_token)
        return self._process_social_user_login(
            tenant_id=payload.tenant_id,
            provider="facebook",
            identity_data=identity_data,
            device_info=payload.device_info,
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

        verify_tenant_active(subscriber.tenant)

        # Revoke old refresh token (Token Rotation)
        self.repo.revoke_refresh_token(payload.refresh_token)

        return self._issue_auth_session(subscriber, device_info=token_record.device_info)

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
