from fastapi import APIRouter, status

from app.dependencies import CurrentSubscriber, FormFile
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
    UpdateSubscriberProfileRequest,
    UserProfileResponse,
    VerifyRegistrationRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
)
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.services.mobile.auth_service import AuthService

router = APIRouter(prefix="/api/v1/mobile/auth", tags=["Mobile Authentication"])
auth_service = AuthService()


# --------------------------------------------------------------------------
# Native Email & Password Authentication Routes
# --------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate Registration & Send Verification Code",
    description="Dispatches a 6-digit OTP code to email to verify registration or link existing Google account.",
)
def register(payload: MobileRegisterRequest):
    return auth_service.initiate_registration(payload)


@router.post(
    "/verify-registration",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Verify Registration Code & Issue Tokens",
    description="Verifies the 6-digit OTP code, creates or smart-links subscriber account, deletes the OTP record immediately, and returns application JWT tokens.",
)
def verify_registration(payload: VerifyRegistrationRequest):
    return auth_service.verify_registration(payload)


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Email & Password Login",
    description="Authenticates registered subscribers using their email address and password.",
)
def login(payload: MobileLoginRequest):
    return auth_service.login_local_subscriber(payload)


@router.post(
    "/forgot-password",
    response_model=ActionSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset Code",
    description="Initiates password reset flow by dispatching a 6-digit OTP code to the subscriber's email.",
)
def forgot_password(payload: ForgotPasswordRequest):
    return auth_service.request_password_reset(payload)


@router.post(
    "/verify-reset-code",
    response_model=VerifyResetCodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Password Reset Code",
    description="Validates the 6-digit OTP code, deletes the OTP record immediately, and returns a 10-minute stateless signed JWT reset_token.",
)
def verify_reset_code(payload: VerifyResetCodeRequest):
    return auth_service.verify_reset_code(payload)


@router.post(
    "/reset-password",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Password via Reset Token",
    description="Validates the cryptographically signed reset_token, sets the new password, and returns fresh JWT tokens for instant auto-login.",
)
def reset_password(payload: ResetPasswordRequest):
    return auth_service.reset_password_with_token(payload)


# --------------------------------------------------------------------------
# Social & Guest Authentication Routes
# --------------------------------------------------------------------------


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
    summary="Dedicated Google OIDC Sign-In",
    description="Exchanges a Google OIDC id_token JWT for application session JWT tokens.",
)
def authenticate_google(payload: GoogleAuthRequest):
    return auth_service.authenticate_google(payload)


@router.post(
    "/facebook",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Dedicated Facebook OAuth Sign-In",
    description="Exchanges a Facebook OAuth access_token for application session JWT tokens.",
)
def authenticate_facebook(payload: FacebookAuthRequest):
    return auth_service.authenticate_facebook(payload)


# --------------------------------------------------------------------------
# Session Lifecycle & Profile Routes
# --------------------------------------------------------------------------


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


@router.patch(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Subscriber Profile Name",
    description="Updates the display name of the authenticated subscriber.",
)
def update_subscriber_profile(
    payload: UpdateSubscriberProfileRequest,
    current_user: CurrentSubscriber,
):
    return auth_service.update_profile_name(
        user_id=current_user["user_id"],
        role=current_user.get("role"),
        payload=payload,
    )


@router.post(
    "/profile/photo",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Subscriber Avatar Photo",
    description="Uploads a new avatar image to Bunny Storage with CDN cache-busting.",
)
def upload_subscriber_avatar(
    current_user: CurrentSubscriber,
    photo: FormFile,
):
    return auth_service.upload_profile_avatar(
        user_id=current_user["user_id"],
        role=current_user.get("role"),
        file=photo,
    )
