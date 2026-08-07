from fastapi import APIRouter, Depends, UploadFile, File, status

from app.dependencies import get_current_admin
from app.schemas.profile_schemas import (
    ProfileResponse,
    ProfileUpdateRequest,
    ProfilePhotoUploadResponse
)
from app.schemas.common_schemas import ActionSuccessResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/v1/admin/profile", tags=["Admin Profile"])
profile_service = ProfileService()

@router.get("", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
def get_creator_profile(current_user: dict = Depends(get_current_admin)):
    """
    GET /api/v1/admin/profile — Retrieves profile details and social links for Settings -> Profile UI.
    """
    return profile_service.get_profile(current_user["user_id"])

@router.put("", response_model=ActionSuccessResponse, status_code=status.HTTP_200_OK)
def update_creator_profile(payload: ProfileUpdateRequest, current_user: dict = Depends(get_current_admin)):
    """
    PUT /api/v1/admin/profile — Updates creator profile attributes and social media links.
    """
    return profile_service.update_profile(current_user["user_id"], payload)

@router.post("/photo", response_model=ProfilePhotoUploadResponse, status_code=status.HTTP_200_OK)
def upload_profile_photo(photo: UploadFile = File(...), current_user: dict = Depends(get_current_admin)):
    """
    POST /api/v1/admin/profile/photo — Uploads avatar photo binary to Bunny Storage Zone and returns CDN avatar URL.
    """
    return profile_service.upload_profile_photo(current_user["user_id"], photo)
