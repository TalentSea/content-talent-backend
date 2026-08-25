from fastapi import APIRouter, Depends

from app.dependencies import get_current_subscriber
from app.schemas.mobile.featured_video_schemas import MobileFeaturedVideoResponse
from app.services.mobile.featured_video_service import MobileFeaturedVideoService

router = APIRouter(prefix="/api/v1/mobile/featured-videos", tags=["Mobile Featured Videos"])
service = MobileFeaturedVideoService()


@router.get(
    "",
    response_model=list[MobileFeaturedVideoResponse],
    summary="Get Mobile Featured Videos Feed",
    description="Retrieves creator featured videos for mobile home screen hero carousel ordered by position, enriched with subscriber interaction flags.",
)
def get_mobile_featured_videos(
    current_subscriber: dict = Depends(get_current_subscriber),
) -> list[MobileFeaturedVideoResponse]:
    creator_id = current_subscriber.get("creator_id")
    subscriber_id = current_subscriber.get("id")

    return service.get_featured_videos(
        creator_id=creator_id, subscriber_id=subscriber_id
    )
