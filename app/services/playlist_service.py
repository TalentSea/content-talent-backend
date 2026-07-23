from app.schemas.playlist_schemas import (
    PlaylistCreateRequest,
    PlaylistCreateResponse,
    PlaylistSummaryResponse,
    PlaylistResponse,
    PlaylistUpdateRequest,
    PlaylistBannerUploadUrlResponse,
    PlaylistItemVideoResponse
)
from app.schemas.common_schemas import PaginatedResponse

class PlaylistService:
    """
    Business logic and cloud orchestration layer for Playlist operations (Peewee ORM).
    """

    def create_playlist(self, user_id: int, payload: PlaylistCreateRequest) -> PlaylistCreateResponse:
        """
        Saves playlist record in DB, links initial video IDs, and returns deterministic banner image_upload_url (playlist_{id}.jpg).
        """
        pass

    def list_user_playlists(self, user_id: int, page: int = 1, limit: int = 20) -> PaginatedResponse[PlaylistSummaryResponse]:
        """
        Fetches paginated creator playlists and returns lightweight summary DTOs containing video_count.
        """
        pass

    def get_playlist_details(self, user_id: int, playlist_id: int, page: int = 1, limit: int = 20) -> PlaylistResponse:
        """
        Fetches single playlist details and a paginated list of attached video DTOs.
        """
        pass

    def update_playlist(self, user_id: int, playlist_id: int, payload: PlaylistUpdateRequest) -> PlaylistResponse:
        """
        Updates playlist textual metadata (name, description) and attached video mappings in DB.
        """
        pass

    def generate_banner_upload_url(self, user_id: int, playlist_id: int) -> PlaylistBannerUploadUrlResponse:
        """
        Generates write-only Bunny Storage URL to overwrite/update deterministic banner asset (playlist_{id}.jpg).
        """
        pass

    def delete_playlist(self, user_id: int, playlist_id: int) -> dict:
        """
        Deletes playlist record and associated junction links from DB via PlaylistRepository.
        """
        pass

    def get_available_videos(self, user_id: int, playlist_id: int, page: int = 1, limit: int = 20) -> PaginatedResponse[PlaylistItemVideoResponse]:
        """
        Fetches a paginated list of creator videos available to be added to the playlist.
        """
        pass
