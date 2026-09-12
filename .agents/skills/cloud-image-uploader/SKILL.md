---
name: cloud-image-uploader
description: Centralized image upload engine rules for Bunny Storage. Enforces global .env size limits, MIME validation, auto-cleanup of replaced cloud files, and CDN cache-busting URLs.
---

# Cloud Image Uploader Engine Skill

## Overview
This skill documents standards for uploading, validating, and managing binary image assets (avatars, video thumbnails, playlist covers, studio logos, and banners) on **Bunny Cloud Storage**.

---

## 1. Centralized Image Upload Standard

All image upload operations across Route and Service layers MUST delegate to `validate_and_upload_image` in `app.utils.image_uploader`:

```python
from app.utils.image_uploader import validate_and_upload_image

cdn_url = validate_and_upload_image(
    file=upload_file,
    storage_path_without_ext=f"assets/branding/logo_{creator_id}_{timestamp}",
    max_size_mb=settings.MAX_LOGO_SIZE_MB,
    old_file_url=branding.logo_url,
    old_file_storage_folder="assets/branding",
)
```

---

## 2. Validation Pipeline

The uploader strictly enforces three sequential validation stages:

1. **Extension & MIME Validation**:
   - Compares the uploaded file's extension against `settings.allowed_image_extensions_tuple` (e.g., `jpg`, `jpeg`, `png`, `webp`, `svg`).
   - If disallowed, raises `HTTP 400 Bad Request ("Disallowed file extension")`.
2. **Size Enforcement**:
   - Reads file stream in chunks or checks `file.size`.
   - Compares total bytes against `max_size_mb * 1024 * 1024`.
   - If exceeded, raises `HTTP 400 Bad Request ("File size exceeds limit of X MB")`.
3. **Stream Rewind**:
   - Always resets file stream pointer (`file.file.seek(0)`) after size inspection before dispatching to Bunny Storage.

---

## 3. Storage Optimization & Cache-Busting

* **Auto-Cleanup (No Orphaned Files)**: When replacing an existing asset (e.g., updating a playlist cover or logo), passing `old_file_url` extracts the previous storage path and sends a `DELETE` request to Bunny Storage, preventing storage bloat and unnecessary storage costs.
* **Deterministic Cache-Busting**: Embed unix timestamps in filenames:
  ```text
  assets/thumbnails/thumb_{video_id}_{int(time.time())}.webp
  ```
  This ensures that when a creator replaces an image, client mobile apps and browsers immediately fetch the fresh asset without being served stale cached images by Bunny CDN.

---

## 4. Size Limits Reference Configuration

| Setting Key | Type | Default | Usage |
| :--- | :---: | :---: | :--- |
| `ALLOWED_IMAGE_EXTENSIONS` | `str` | `jpg,jpeg,png,webp,svg` | Comma-delimited list of accepted image formats. |
| `MAX_AVATAR_SIZE_MB` | `int` | `2` | User and creator profile avatars. |
| `MAX_THUMBNAIL_SIZE_MB` | `int` | `5` | Video custom poster thumbnails. |
| `MAX_PLAYLIST_COVER_SIZE_MB` | `int` | `5` | Playlist covers. |
| `MAX_LOGO_SIZE_MB` | `int` | `5` | Studio branding logos. |
| `MAX_BANNER_SIZE_MB` | `int` | `10` | Studio hero cover banners. |
