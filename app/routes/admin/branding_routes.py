from fastapi import APIRouter, status

from app.dependencies import CurrentAdmin, FormFile
from app.schemas.shared.branding_schemas import (
    BrandingBannerUploadResponse,
    BrandingLogoUploadResponse,
    BrandingResponse,
    BrandingUpdateRequest,
)
from app.services.shared.branding_service import BrandingService

router = APIRouter(prefix="/api/v1/admin/branding", tags=["Admin Branding"])
branding_service = BrandingService()


@router.get("", response_model=BrandingResponse, status_code=status.HTTP_200_OK)
def get_creator_branding(current_user: CurrentAdmin):
    """
    GET /api/v1/admin/branding — Retrieves creator identity, tagline, description, banner, and logo for Branding UI.
    """
    return branding_service.get_branding(current_user["user_id"])


@router.put("", response_model=BrandingResponse, status_code=status.HTTP_200_OK)
def update_creator_branding(
    payload: BrandingUpdateRequest, current_user: CurrentAdmin
):
    """
    PUT /api/v1/admin/branding — Updates creator branding text attributes and returns updated BrandingResponse.
    """
    return branding_service.update_branding(current_user["user_id"], payload)


@router.post(
    "/logo",
    response_model=BrandingLogoUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_creator_logo(current_user: CurrentAdmin, logo: FormFile):
    """
    POST /api/v1/admin/branding/logo — Uploads creator logo image (PNG, SVG, JPG, WebP) to Bunny Storage and returns CDN URL.
    """
    return branding_service.upload_logo(current_user["user_id"], logo)


@router.post(
    "/banner",
    response_model=BrandingBannerUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_creator_banner(current_user: CurrentAdmin, banner: FormFile):
    """
    POST /api/v1/admin/branding/banner — Uploads creator cover banner image to Bunny Storage and returns CDN URL.
    """
    return branding_service.upload_banner(current_user["user_id"], banner)
