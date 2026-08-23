from fastapi import APIRouter, Response, status

from app.dependencies import CurrentSubscriber
from app.schemas.branding_schemas import BrandingResponse
from app.services.branding_service import BrandingService

router = APIRouter(prefix="/api/v1/mobile/branding", tags=["Mobile Branding"])
branding_service = BrandingService()


@router.get(
    "",
    response_model=BrandingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Mobile Studio Branding Identity",
    description="Retrieves studio branding identity for mobile subscribers. Accessible by Guests and Subscribers.",
)
def get_mobile_branding(
    current_subscriber: CurrentSubscriber, response: Response
) -> BrandingResponse:
    """
    Returns public studio branding assets for mobile app rendering.
    Sets Cache-Control headers to optimize client-side app cold boot speeds.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    return branding_service.get_public_mobile_branding(
        creator_id=current_subscriber.get("creator_id")
    )
