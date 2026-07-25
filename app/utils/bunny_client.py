import logging
import requests
from fastapi import HTTPException, status
from app.config import get_settings

logger = logging.getLogger(__name__)

def create_bunny_video(title: str) -> dict:
    """
    Issues an HTTP POST request to Bunny Stream API to reserve an empty video container slot and return a bunny_video_id GUID.
    """
    settings = get_settings()
    url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos"
    headers = {
        "AccessKey": settings.BUNNY_STREAM_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json={"title": title}, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        if response.status_code in (401, 403):
            logger.error(f"Invalid Bunny Stream API Key or Library ID (HTTP {response.status_code}). Please verify credentials in .env")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid Bunny Stream API Key or Library ID (HTTP {response.status_code})"
            )
        logger.error(f"Bunny Stream POST Error ({response.status_code}): {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create video container on Bunny Stream (HTTP {response.status_code})"
        )
    except requests.RequestException as e:
        logger.error(f"Bunny Stream connection exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bunny Stream service is currently unreachable"
        )

def get_bunny_video_status(bunny_video_id: str) -> dict:
    """
    Issues an HTTP GET request to Bunny Stream API to fetch live encodeProgress percentage and resolution availability.
    """
    settings = get_settings()
    url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{bunny_video_id}"
    headers = {
        "AccessKey": settings.BUNNY_STREAM_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        if response.status_code in (401, 403):
            logger.error(f"Invalid Bunny Stream API Key or Library ID (HTTP {response.status_code})")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid Bunny Stream API Key or Library ID (HTTP {response.status_code})"
            )
        logger.error(f"Bunny Stream GET Error ({response.status_code}): {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch video status from Bunny Stream (HTTP {response.status_code})"
        )
    except requests.RequestException as e:
        logger.error(f"Bunny Stream status fetch exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bunny Stream service is currently unreachable"
        )

def delete_bunny_video(bunny_video_id: str) -> bool:
    """
    Issues an HTTP DELETE request to Bunny Stream API to permanently remove a video container and encoded video streams.
    """
    settings = get_settings()
    url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{bunny_video_id}"
    headers = {
        "AccessKey": settings.BUNNY_STREAM_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Bunny Stream DELETE exception: {str(e)}")
        return False

def delete_bunny_storage_file(file_path: str) -> bool:
    """
    Issues an HTTP DELETE request to Bunny Storage API to remove a physical thumbnail or asset file from cloud storage.
    """
    settings = get_settings()
    clean_path = file_path.lstrip("/")
    url = f"https://storage.bunnycdn.com/{settings.BUNNY_STORAGE_ZONE_NAME}/{clean_path}"
    headers = {
        "AccessKey": settings.BUNNY_STORAGE_PASSWORD
    }

    try:
        response = requests.delete(url, headers=headers, timeout=10)
        return response.status_code in (200, 204)
    except requests.RequestException as e:
        logger.error(f"Bunny Storage DELETE exception: {str(e)}")
        return False

def upload_bunny_stream_thumbnail(bunny_video_id: str, file_bytes: bytes, content_type: str = "image/jpeg") -> bool:
    """
    Issues an HTTP POST request to Bunny Stream API to upload/overwrite the primary cover frame (slot 0).
    """
    settings = get_settings()
    url = f"https://video.bunnycdn.com/library/{settings.BUNNY_STREAM_LIBRARY_ID}/videos/{bunny_video_id}/thumbnail"
    headers = {
        "AccessKey": settings.BUNNY_STREAM_API_KEY,
        "Content-Type": content_type
    }

    try:
        response = requests.post(url, data=file_bytes, headers=headers, timeout=15)
        if response.status_code == 200:
            return True
        logger.error(f"Bunny Stream thumbnail upload error ({response.status_code}): {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload cover thumbnail to Bunny Stream (HTTP {response.status_code})"
        )
    except requests.RequestException as e:
        logger.error(f"Bunny Stream thumbnail upload exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bunny Stream service is currently unreachable"
        )

def upload_bunny_storage_file(file_path: str, file_bytes: bytes, content_type: str = "image/jpeg") -> bool:
    """
    Issues an HTTP PUT request to Bunny Storage API to upload a physical image file to cloud storage.
    """
    settings = get_settings()
    clean_path = file_path.lstrip("/")
    url = f"https://storage.bunnycdn.com/{settings.BUNNY_STORAGE_ZONE_NAME}/{clean_path}"
    headers = {
        "AccessKey": settings.BUNNY_STORAGE_PASSWORD,
        "Content-Type": content_type
    }

    try:
        response = requests.put(url, data=file_bytes, headers=headers, timeout=15)
        if response.status_code in (200, 201):
            return True
        logger.error(f"Bunny Storage upload error ({response.status_code}): {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload asset to Bunny Storage (HTTP {response.status_code})"
        )
    except requests.RequestException as e:
        logger.error(f"Bunny Storage upload exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bunny Storage service is currently unreachable"
        )



