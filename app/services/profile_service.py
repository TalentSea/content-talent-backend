import logging
import time
from typing import Optional
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile_schemas import (
    ProfileResponse,
    ProfileUpdateRequest,
    SocialLinksSchema,
    ProfilePhotoUploadResponse
)
from app.schemas.common_schemas import ActionSuccessResponse
from app.utils.bunny_client import (
    upload_bunny_storage_file,
    delete_bunny_storage_file
)

logger = logging.getLogger(__name__)

class ProfileService:
    """
    Business logic layer for Creator Admin Profile & Avatar operations.
    """

    def __init__(self):
        self.repo = ProfileRepository()

    def get_profile(self, admin_id: int) -> ProfileResponse:
        """
        Retrieves detailed profile information and social links for authenticated creator admin.
        """
        admin = self.repo.get_profile_by_admin_id(admin_id)
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator profile not found")

        social_links = SocialLinksSchema(
            twitter=admin.twitter_url,
            youtube=admin.youtube_url,
            instagram=admin.instagram_url
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
            updated_at=admin.updated_at
        )

    def update_profile(self, admin_id: int, payload: ProfileUpdateRequest) -> ActionSuccessResponse:
        """
        Updates creator profile information and social links in DB.
        """
        update_data = payload.model_dump(exclude_unset=True)
        admin = self.repo.update_profile(admin_id, update_data)
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator profile not found")

        return ActionSuccessResponse(status="success")

    def upload_profile_photo(self, admin_id: int, file: UploadFile) -> ProfilePhotoUploadResponse:
        """
        Uploads avatar image to Bunny Storage (assets/avatars/avatar_{admin_id}_{timestamp}.{ext}) with CDN cache-busting.
        """
        admin = self.repo.get_profile_by_admin_id(admin_id)
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator profile not found")

        allowed_mime_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        content_type = (file.content_type or "").lower()
        if content_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{file.content_type}'. Only JPEG, PNG, and WebP image files are allowed."
            )

        file_bytes = file.file.read()
        if len(file_bytes) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum allowed limit of 2MB."
            )

        settings = get_settings()
        pull_zone = settings.BUNNY_STORAGE_PULL_ZONE_URL.rstrip("/")

        # Delete previous avatar file from Bunny Storage if present on CDN
        if admin.avatar_url and "talentsea77999.b-cdn.net" in admin.avatar_url:
            try:
                old_filename = admin.avatar_url.split('/')[-1]
                delete_bunny_storage_file(f"assets/avatars/{old_filename}")
            except Exception as e:
                logger.warning(f"Failed to delete old avatar file for admin {admin_id}: {str(e)}")

        ext = content_type.split('/')[-1]
        if ext == "jpeg":
            ext = "jpg"
        timestamp = int(time.time())
        filename = f"avatar_{admin_id}_{timestamp}.{ext}"
        storage_path = f"assets/avatars/{filename}"

        upload_bunny_storage_file(storage_path, file_bytes, content_type)

        avatar_url = f"{pull_zone}/{storage_path}"
        self.repo.update_avatar_url(admin_id, avatar_url)

        return ProfilePhotoUploadResponse(avatar_url=avatar_url)
