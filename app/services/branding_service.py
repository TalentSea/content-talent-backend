import time

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.branding_repository import BrandingRepository
from app.schemas.branding_schemas import (
    BrandingBannerUploadResponse,
    BrandingLogoUploadResponse,
    BrandingResponse,
    BrandingUpdateRequest,
)
from app.utils.image_uploader import validate_and_upload_image


class BrandingService:
    """
    Business service layer managing creator studio branding, identity attributes, and cloud asset uploads.
    """

    def __init__(self, repo: BrandingRepository | None = None) -> None:
        self.repo = repo or BrandingRepository()

    def _to_branding_response(self, branding) -> BrandingResponse:
        """Helper to map a Branding ORM instance to a BrandingResponse DTO."""
        return BrandingResponse(
            creator_name=branding.creator_name,
            tagline=branding.tagline,
            description=branding.description,
            banner_url=branding.banner_url,
            logo_url=branding.logo_url,
            updated_at=branding.updated_at,
        )

    def get_branding(self, user_id: int) -> BrandingResponse:
        """
        Retrieves current branding identity and assets for the authenticated creator.
        Initializes an empty default record if one does not yet exist.
        """
        branding = self.repo.get_or_create_branding(user_id)
        return self._to_branding_response(branding)

    def get_public_mobile_branding(
        self, creator_id: int | None = None
    ) -> BrandingResponse:
        """
        Retrieves studio branding identity for mobile subscribers on app startup.
        Raises HTTP 404 NOT FOUND if creator branding has not been created in database.
        """
        branding = self.repo.get_first_branding(creator_id=creator_id)
        if not branding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator branding not found",
            )
        return self._to_branding_response(branding)

    def update_branding(
        self, user_id: int, payload: BrandingUpdateRequest
    ) -> BrandingResponse:
        """
        Applies partial updates to creator identity text attributes and returns the updated BrandingResponse.
        """
        update_data = payload.model_dump(exclude_unset=True)
        updated_branding = self.repo.update_branding_text(user_id, update_data)
        return self._to_branding_response(updated_branding)

    def upload_logo(
        self, user_id: int, file: UploadFile
    ) -> BrandingLogoUploadResponse:
        """
        Validates and uploads a creator logo image to Bunny Storage.
        """
        branding = self.repo.get_or_create_branding(user_id)
        settings = get_settings()
        timestamp = int(time.time())

        cdn_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/branding/logo_{user_id}_{timestamp}",
            max_size_mb=settings.MAX_LOGO_SIZE_MB,
            old_file_url=branding.logo_url,
            old_file_storage_folder="assets/branding",
        )
        self.repo.update_logo_url(user_id, cdn_url)
        return BrandingLogoUploadResponse(logo_url=cdn_url)

    def upload_banner(
        self, user_id: int, file: UploadFile
    ) -> BrandingBannerUploadResponse:
        """
        Validates and uploads a creator cover banner image to Bunny Storage.
        """
        branding = self.repo.get_or_create_branding(user_id)
        settings = get_settings()
        timestamp = int(time.time())

        cdn_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/branding/banner_{user_id}_{timestamp}",
            max_size_mb=settings.MAX_BANNER_SIZE_MB,
            old_file_url=branding.banner_url,
            old_file_storage_folder="assets/branding",
        )
        self.repo.update_banner_url(user_id, cdn_url)
        return BrandingBannerUploadResponse(banner_url=cdn_url)
