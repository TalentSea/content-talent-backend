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
    Business logic layer for Creator Profile & Avatar operations.
    """

    def __init__(self):
        self.repo = ProfileRepository()

    def get_profile(self, user_id: int) -> ProfileResponse:
        """
        Retrieves detailed profile information and social links for authenticated creator.
        """
        user = self.repo.get_profile_by_user_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator profile not found")

        social_links = SocialLinksSchema(
            twitter=user.twitter_url,
            youtube=user.youtube_url,
            instagram=user.instagram_url
        )

        return ProfileResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            bio=user.bio,
            website=user.website,
            phone=user.phone,
            location=user.location,
            avatar_url=user.avatar_url,
            social_links=social_links,
            updated_at=user.updated_at
        )

    def update_profile(self, user_id: int, payload: ProfileUpdateRequest) -> ActionSuccessResponse:
        """
        Updates creator profile information and social links in DB.
        """
        update_data = payload.model_dump(exclude_unset=True)
        user = self.repo.update_profile(user_id, update_data)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator profile not found")

        return ActionSuccessResponse(status="success")

    def upload_profile_photo(self, user_id: int, file: UploadFile) -> ProfilePhotoUploadResponse:
        """
        Uploads avatar image to Bunny Storage (assets/avatars/avatar_{user_id}_{timestamp}.{ext}) with CDN cache-busting.
        """
        user = self.repo.get_profile_by_user_id(user_id)
        if not user:
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
        if user.avatar_url and "talentsea77999.b-cdn.net" in user.avatar_url:
            try:
                old_filename = user.avatar_url.split('/')[-1]
                delete_bunny_storage_file(f"assets/avatars/{old_filename}")
            except Exception as e:
                logger.warning(f"Failed to delete old avatar file for user {user_id}: {str(e)}")

        timestamp = int(time.time())
        ext = "png" if "png" in content_type else ("webp" if "webp" in content_type else "jpg")
        avatar_path = f"assets/avatars/avatar_{user_id}_{timestamp}.{ext}"
        avatar_url = f"{pull_zone}/{avatar_path}"

        upload_bunny_storage_file(avatar_path, file_bytes, content_type)

        self.repo.update_avatar_url(user_id, avatar_url)
        return ProfilePhotoUploadResponse(avatar_url=avatar_url)
