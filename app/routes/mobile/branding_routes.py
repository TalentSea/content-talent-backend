from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.schemas.shared.branding_schemas import BrandingResponse
from app.services.shared.branding_service import BrandingService

router = APIRouter(prefix="/api/v1/mobile/branding", tags=["Mobile Branding"])
branding_service = BrandingService()


@router.get(
    "",
    response_model=BrandingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Mobile Studio Branding Identity & Theme",
    description="Retrieves studio branding identity, visual assets, and theme color tokens for mobile apps without authentication.",
)
def get_mobile_branding(
    x_tenant_id: Annotated[int, Header(alias="X-Tenant-Id")], response: Response
) -> BrandingResponse:
    """
    Returns public studio branding assets and theme color palette for mobile app rendering.
    Sets Cache-Control headers to optimize client-side app cold boot speeds.
    """

    response.headers["Cache-Control"] = "public, max-age=3600"
    return branding_service.get_public_mobile_branding(tenant_id=x_tenant_id)
