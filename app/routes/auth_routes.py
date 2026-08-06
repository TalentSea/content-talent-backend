from fastapi import APIRouter, Depends, status
from app.schemas.auth_schemas import (
    GoogleAuthRequest,
    FacebookAuthRequest,
    RefreshTokenRequest,
    AuthTokenResponse,
    UserProfileResponse
)
from app.schemas.common_schemas import ActionSuccessResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Mobile Social Authentication"])
auth_service = AuthService()

@router.post(
    "/google",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Dedicated Google OIDC Sign-In",
    description="Exchanges a Google OIDC id_token JWT for application session JWT tokens."
)
def authenticate_google(payload: GoogleAuthRequest):
    return auth_service.authenticate_google(payload)

@router.post(
    "/facebook",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Dedicated Facebook OAuth Sign-In",
    description="Exchanges a Facebook OAuth access_token for application session JWT tokens."
)
def authenticate_facebook(payload: FacebookAuthRequest):
    return auth_service.authenticate_facebook(payload)

@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Silent Access Token Refresh",
    description="Issues a fresh access token and rotated refresh token using an active refresh token."
)
def refresh_token(payload: RefreshTokenRequest):
    return auth_service.refresh_access_token(payload)

@router.post(
    "/logout",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke Session Refresh Token",
    description="Invalidates an active refresh token in database upon user logout."
)
def logout_session(payload: RefreshTokenRequest):
    return auth_service.logout_session(payload)

@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User Profile",
    description="Retrieves profile metadata for the current authenticated subscriber."
)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    return auth_service.get_current_user_profile(user_id)
