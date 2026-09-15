from fastapi import APIRouter, status

from app.dependencies import CurrentSubscriber, OptionalSubscriber
from app.schemas.mobile.auth_schemas import (
    AuthTokenResponse,
    FacebookAuthRequest,
    GoogleAuthRequest,
    GuestAuthRequest,
    RefreshTokenRequest,
    UserProfileResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.mobile.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Mobile Social Authentication"])
auth_service = AuthService()


@router.post(
    "/guest",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Anonymous Guest Session (Skip Signup)",
    description="Issues an application session for anonymous guest users skipping social login on app launch.",
)
def authenticate_guest(payload: GuestAuthRequest):
    return auth_service.authenticate_guest(payload)


@router.post(
    "/google",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Dedicated Google OIDC Sign-In & Account Upgrade",
    description="Exchanges a Google OIDC id_token JWT for application session JWT tokens. Upgrades active Guest account in-place if Bearer token is provided.",
)
def authenticate_google(
    payload: GoogleAuthRequest, optional_subscriber: OptionalSubscriber = None
):
    guest_id = optional_subscriber.get("user_id") if optional_subscriber else None
    return auth_service.authenticate_google(payload, guest_subscriber_id=guest_id)


@router.post(
    "/facebook",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Dedicated Facebook OAuth Sign-In & Account Upgrade",
    description="Exchanges a Facebook OAuth access_token for application session JWT tokens. Upgrades active Guest account in-place if Bearer token is provided.",
)
def authenticate_facebook(
    payload: FacebookAuthRequest, optional_subscriber: OptionalSubscriber = None
):
    guest_id = optional_subscriber.get("user_id") if optional_subscriber else None
    return auth_service.authenticate_facebook(payload, guest_subscriber_id=guest_id)


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Silent Access Token Refresh",
    description="Issues a fresh access token and rotated refresh token using an active refresh token.",
)
def refresh_token(payload: RefreshTokenRequest):
    return auth_service.refresh_access_token(payload)


@router.post(
    "/logout",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke Session Refresh Token",
    description="Invalidates an active refresh token in database upon user logout.",
)
def logout_session(payload: RefreshTokenRequest):
    return auth_service.logout_session(payload)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User Profile",
    description="Retrieves profile metadata for the current authenticated subscriber.",
)
def get_current_user_profile(current_user: CurrentSubscriber):
    user_id = current_user.get("user_id")
    return auth_service.get_current_user_profile(user_id)
