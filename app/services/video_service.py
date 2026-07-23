from app.schemas.video_schemas import (
    VideoInitiateRequest,
    VideoInitiateResponse,
    VideoResponse,
    VideoUpdateRequest,
    ThumbnailUploadUrlRequest,
    ThumbnailUploadUrlResponse,
    SelectMainThumbnailRequest,
    DeleteThumbnailRequest,
    BunnyWebhookPayload
)
from app.schemas.common_schemas import PaginatedResponse

class VideoService:
    """
    Business logic and cloud orchestration layer for Video operations (Peewee ORM).
    """

    def initiate_video_upload(self, user_id: int, payload: VideoInitiateRequest) -> VideoInitiateResponse:
        """
        Orchestrates Bunny container reservation, HMAC TUS signature generation, CDN URL pre-calculation, and DB insertion.
        """
        pass

    def handle_bunny_webhook(self, payload: BunnyWebhookPayload) -> dict:
        """
        Processes status code state machine (0 to 10) from Bunny Stream webhook events and updates database state.
        """
        pass

    def get_video_details(self, user_id: int, video_id: int) -> VideoResponse:
        """
        Fetches video details from DB; if state is ENCODING, queries Bunny Stream API for live encodeProgress sync.
        """
        pass

    def list_user_videos(self, user_id: int, page: int = 1, limit: int = 20) -> PaginatedResponse[VideoResponse]:
        """
        Fetches a paginated list of videos created by the authenticated creator and returns a PaginatedResponse envelope.
        """
        pass

    def update_video_metadata(self, user_id: int, video_id: int, payload: VideoUpdateRequest) -> VideoResponse:
        """
        Validates ownership and applies partial textual metadata updates (title, description, category, tags) in DB.
        """
        pass

    def generate_thumbnail_upload_url(self, user_id: int, video_id: int, payload: ThumbnailUploadUrlRequest) -> ThumbnailUploadUrlResponse:
        """
        Evaluates 0-indexed slot (0 for Bunny Stream API, 1/2 for Bunny Storage API) and returns write-only image_upload_url.
        """
        pass

    def select_main_thumbnail(self, user_id: int, video_id: int, payload: SelectMainThumbnailRequest) -> VideoResponse:
        """
        Executes thumbnail swapping logic between main cover and alt thumbnails in DB.
        """
        pass

    def delete_alternative_thumbnail(self, user_id: int, video_id: int, payload: DeleteThumbnailRequest) -> VideoResponse:
        """
        Issues HTTP DELETE to Bunny Storage API to remove physical cloud image and updates DB list via VideoRepository.
        """
        pass

    def delete_video_asset(self, user_id: int, video_id: int) -> dict:
        """
        Issues HTTP DELETE to Bunny Stream API to remove cloud video container and drops video record from DB.
        """
        pass
