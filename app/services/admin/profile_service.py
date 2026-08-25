import time

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.admin.profile_repository import ProfileRepository
from app.schemas.shared.common_schemas import ActionSuccessResponse
from app.schemas.admin.profile_schemas import (
    ProfilePhotoUploadResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    SocialLinksSchema,
)
from app.utils.image_uploader import validate_and_upload_image


class ProfileService:
    """
    Business logic layer for Creator Admin Profile & Avatar operations.
    """

    def __init__(self, repo: ProfileRepository | None = None) -> None:
        self.repo = repo or ProfileRepository()

    def get_profile(self, admin_id: int) -> ProfileResponse:
        """
        Retrieves profile info and social links for Settings -> Profile UI page.
        """
        admin = self.repo.get_profile_by_admin_id(admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator account associated with this session was not found",
            )

        social_links = SocialLinksSchema(
            twitter=admin.twitter_url,
            youtube=admin.youtube_url,
            instagram=admin.instagram_url,
        )

        return ProfileResponse(
            first_name=admin.first_name,
            last_name=admin.last_name,
            email=admin.email,
            bio=admin.bio,
            website=admin.website,
            phone=admin.phone,
            location=admin.location,
            avatar_url=admin.avatar_url,
            social_links=social_links,
            updated_at=admin.updated_at,
        )

    def update_profile(
        self, admin_id: int, payload: ProfileUpdateRequest
    ) -> ActionSuccessResponse:
        """
        Updates creator profile and social links in database (excluding email).
        """
        update_data = {}
        for field in [
            "first_name",
            "last_name",
            "bio",
            "website",
            "phone",
            "location",
        ]:
            val = getattr(payload, field)
            if val is not None:
                update_data[field] = val

        if payload.social_links is not None:
            if payload.social_links.twitter is not None:
                update_data["twitter_url"] = payload.social_links.twitter
            if payload.social_links.youtube is not None:
                update_data["youtube_url"] = payload.social_links.youtube
            if payload.social_links.instagram is not None:
                update_data["instagram_url"] = payload.social_links.instagram

        success = self.repo.update_profile(admin_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator account associated with this session was not found",
            )

        return ActionSuccessResponse(status="success")

    def upload_profile_photo(
        self, admin_id: int, file: UploadFile
    ) -> ProfilePhotoUploadResponse:
        """
        Uploads avatar image to Bunny Storage (assets/avatars/avatar_{admin_id}_{timestamp}.{ext}) with CDN cache-busting.
        """
        admin = self.repo.get_profile_by_admin_id(admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator account associated with this session was not found",
            )

        settings = get_settings()
        timestamp = int(time.time())

        avatar_url = validate_and_upload_image(
            file=file,
            storage_path_without_ext=f"assets/avatars/avatar_{admin_id}_{timestamp}",
            max_size_mb=settings.MAX_AVATAR_SIZE_MB,
            old_file_url=admin.avatar_url,
            old_file_storage_folder="assets/avatars",
        )

        self.repo.update_avatar_url(admin_id, avatar_url)
        return ProfilePhotoUploadResponse(avatar_url=avatar_url)
