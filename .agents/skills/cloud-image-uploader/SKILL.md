---
name: cloud-image-uploader
description: Centralized image upload engine rules for Bunny Storage. Enforces global .env size limits, MIME validation, auto-cleanup of replaced cloud files, and CDN cache-busting URLs.
---

# Cloud Image Uploader Engine Skill

## Overview
This skill documents standards for uploading, validating, and managing binary image assets (avatars, thumbnails, playlist covers, studio logos, and banners) on **Bunny Cloud Storage**.

---

## 1. Centralized Image Upload Pattern

All image uploads across services MUST invoke `validate_and_upload_image` from `app.utils.image_uploader`:

```python
from app.utils.image_uploader import validate_and_upload_image

cdn_url = validate_and_upload_image(
    file=file,
    storage_path_without_ext=f"assets/branding/logo_{user_id}_{timestamp}",
    max_size_mb=get_settings().MAX_LOGO_SIZE_MB,
    old_file_url=branding.logo_url,
    old_file_storage_folder="assets/branding",
)
```

---

## 2. Global `.env` Configuration
Image limits and formats MUST be configurable via environment variables in `app/config.py`:
- `ALLOWED_IMAGE_EXTENSIONS`: Comma-separated list (`jpg,jpeg,png,webp,svg`).
- `MAX_AVATAR_SIZE_MB`: Maximum size for user/admin avatars.
- `MAX_THUMBNAIL_SIZE_MB`: Maximum size for video custom thumbnails.
- `MAX_PLAYLIST_COVER_SIZE_MB`: Maximum size for playlist covers.
- `MAX_LOGO_SIZE_MB`: Maximum size for studio branding logos.
- `MAX_BANNER_SIZE_MB`: Maximum size for studio cover banners.

---

## 3. Storage Cleanup & Cache-Busting
- **Auto-Cleanup**: When replacing an asset, pass `old_file_url` to prevent orphaned storage bloat on Bunny Storage.
- **Cache-Busting**: Embed unix timestamps (`{identifier}_{timestamp}.{ext}`) in filenames so CDN caches immediately reflect new uploads without stale caching issues.
