import base64
import hashlib
import hmac
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


def _generate_bunny_token(security_key: str, path: str, expires_timestamp: int) -> str:
    """
    Generates Bunny CDN Advanced Token Authentication (HMAC-SHA256 Base64URL with HS256- prefix).
    """
    message = f"{path}{expires_timestamp}"
    raw_hmac = hmac.new(
        security_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).digest()
    b64_token = (
        base64.b64encode(raw_hmac)
        .decode("utf-8")
        .replace("+", "-")
        .replace("/", "_")
        .rstrip("=")
    )
    return f"HS256-{b64_token}"


def generate_signed_playback_url(
    bunny_pull_zone_url: str,
    bunny_video_id: str,
    token_security_key: str,
    expires_in_seconds: int | None = None,
) -> str:
    """
    Generates a time-bound, presigned HLS playback URL using Bunny CDN Path-Based Token Authentication.
    Embeds the token into the URL path prefix so that both Web browsers and Mobile players
    automatically authorize all sub-resolution playlists and .ts video chunks without 403 errors.
    """
    if expires_in_seconds is None:
        expires_in_seconds = get_settings().BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS
    expires_timestamp = int(time.time()) + expires_in_seconds
    
    dir_path = f"/{bunny_video_id}/"
    token = _generate_bunny_token(token_security_key, dir_path, expires_timestamp)
    base_url = bunny_pull_zone_url.rstrip("/")
    return f"{base_url}/bcdn_token={token}&expires={expires_timestamp}/{bunny_video_id}/playlist.m3u8"


def generate_signed_mp4_url(
    bunny_pull_zone_url: str,
    bunny_video_id: str,
    resolution: str,
    token_security_key: str,
    expires_in_seconds: int | None = None,
) -> str:
    """
    Generates a time-bound presigned MP4 download URL (play_<resolution>.mp4?token=...&expires=...).
    Uses Bunny CDN Advanced Token Authentication (HMAC-SHA256).
    """
    if expires_in_seconds is None:
        expires_in_seconds = get_settings().BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS
    expires_timestamp = int(time.time()) + expires_in_seconds
    clean_res = str(resolution).strip()
    if not clean_res.endswith("p"):
        clean_res = f"{clean_res}p"
    path = f"/{bunny_video_id}/play_{clean_res}.mp4"

    token = _generate_bunny_token(token_security_key, path, expires_timestamp)
    base_url = bunny_pull_zone_url.rstrip("/")
    return f"{base_url}{path}?token={token}&expires={expires_timestamp}"
