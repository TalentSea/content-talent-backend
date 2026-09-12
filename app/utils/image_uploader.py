import logging

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.utils.bunny_client import (
    delete_bunny_storage_file,
    upload_bunny_storage_file,
)

logger = logging.getLogger(__name__)

MIME_TO_EXT_MAP = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}


def validate_and_upload_image(
    file: UploadFile,
    storage_path_without_ext: str,
    max_size_mb: int,
    old_file_url: str | None = None,
    old_file_storage_folder: str | None = None,
) -> str:
    """
    Unified enterprise utility to validate and upload images to Bunny Storage.

    1. Validates Content-Type and file extension against global ALLOWED_IMAGE_EXTENSIONS from .env.
    2. Enforces maximum file size limit (max_size_mb).
    3. Optionally deletes the previous cloud storage file (old_file_url) to avoid orphaned file bloat.
    4. Uploads binary data to Bunny Cloud Storage Zone.
    5. Returns the fully formatted public CDN URL.
    """
    settings = get_settings()
    allowed_extensions = settings.allowed_image_extensions_tuple

    content_type = (file.content_type or "").lower()
    ext = MIME_TO_EXT_MAP.get(content_type)

    if not ext and file.filename:
        fn_ext = file.filename.split(".")[-1].lower()
        if fn_ext in ("png", "svg", "jpg", "jpeg", "webp"):
            ext = "jpg" if fn_ext == "jpeg" else fn_ext

    # Check extension against global allowed extensions tuple
    normalized_allowed = tuple("jpg" if e == "jpeg" else e for e in allowed_extensions)
    if not ext or ext not in normalized_allowed:
        allowed_str = ", ".join(e.upper() for e in allowed_extensions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Only {allowed_str} image files under {max_size_mb}MB are allowed.",
        )

    # Validate file size
    file_bytes = file.file.read()
    max_bytes = max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {max_size_mb}MB.",
        )

    pull_zone = settings.BUNNY_STORAGE_PULL_ZONE_URL.rstrip("/")

    # Optional old file cleanup on Bunny Storage
    if old_file_url and "b-cdn.net" in old_file_url:
        try:
            old_filename = old_file_url.split("/")[-1]
            folder_prefix = (
                f"{old_file_storage_folder.rstrip('/')}/"
                if old_file_storage_folder
                else ""
            )
            delete_bunny_storage_file(f"{folder_prefix}{old_filename}")
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to delete replaced image asset %s: %s",
                old_file_url,
                e,
            )

    # Full cloud destination path
    dest_path = f"{storage_path_without_ext.lstrip('/')}.{ext}"

    upload_bunny_storage_file(
        file_path=dest_path,
        file_bytes=file_bytes,
        content_type=content_type or f"image/{ext}",
    )

    return f"{pull_zone}/{dest_path}"
