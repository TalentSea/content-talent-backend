import hashlib
import time

from app.config import get_settings


def generate_tus_signature(
    library_id: str,
    bunny_api_key: str,
    video_id: str,
    expires_in_seconds: int | None = None,
) -> tuple[str, int]:
    """
    Computes a SHA-256 HMAC signature required by Bunny TUS resumable streaming protocol.
    Formula: SHA256(library_id + bunny_api_key + expiration_time + video_id)
    Returns (signature_hash, expiration_timestamp).
    """
    if expires_in_seconds is None:
        expires_in_seconds = get_settings().BUNNY_TUS_UPLOAD_SIGNATURE_EXPIRE_SECONDS
    expiration_timestamp = int(time.time()) + expires_in_seconds
    to_hash = f"{library_id}{bunny_api_key}{expiration_timestamp}{video_id}"
    signature = hashlib.sha256(to_hash.encode("utf-8")).hexdigest()
    return signature, expiration_timestamp


def generate_signed_playback_url(
    bunny_pull_zone_url: str,
    bunny_video_id: str,
    token_security_key: str,
    expires_in_seconds: int | None = None,
) -> str:
    """
    Generates a time-bound, presigned HLS playback URL (playlist.m3u8?token=...&expires=...).
    Prevents unauthorized hotlinking, stream piracy, and permanent URL sharing.
    """
    if expires_in_seconds is None:
        expires_in_seconds = get_settings().BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS
    expires_timestamp = int(time.time()) + expires_in_seconds
    path = f"/{bunny_video_id}/playlist.m3u8"

    to_hash = f"{token_security_key}{path}{expires_timestamp}"
    token_hash = hashlib.md5(to_hash.encode("utf-8")).hexdigest()

    base_url = bunny_pull_zone_url.rstrip("/")
    return f"{base_url}{path}?token={token_hash}&expires={expires_timestamp}"


def generate_signed_mp4_url(
    bunny_pull_zone_url: str,
    bunny_video_id: str,
    resolution: str,
    token_security_key: str,
    expires_in_seconds: int | None = None,
) -> str:
    """
    Generates a time-bound presigned MP4 download URL (play_<resolution>.mp4?token=...&expires=...).
    Example: play_720p.mp4
    """
    if expires_in_seconds is None:
        expires_in_seconds = get_settings().BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS
    expires_timestamp = int(time.time()) + expires_in_seconds
    clean_res = str(resolution).strip()
    if not clean_res.endswith("p"):
        clean_res = f"{clean_res}p"
    path = f"/{bunny_video_id}/play_{clean_res}.mp4"

    to_hash = f"{token_security_key}{path}{expires_timestamp}"
    token_hash = hashlib.md5(to_hash.encode("utf-8")).hexdigest()

    base_url = bunny_pull_zone_url.rstrip("/")
    return f"{base_url}{path}?token={token_hash}&expires={expires_timestamp}"
