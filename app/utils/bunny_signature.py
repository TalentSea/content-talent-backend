import hashlib
import time

def generate_tus_signature(library_id: str, bunny_api_key: str, expiration_time: int, video_id: str) -> str:
    """
    Computes a SHA-256 HMAC signature required by Bunny TUS resumable streaming protocol.
    Formula: SHA256(library_id + bunny_api_key + expiration_time + video_id)
    """
    pass

def generate_signed_playback_url(bunny_pull_zone_url: str, bunny_video_id: str, token_security_key: str, expires_in_seconds: int = 7200) -> str:
    """
    Generates a time-bound, presigned HLS playback URL (playlist.m3u8?token=...&expires=...).
    Prevents unauthorized hotlinking, stream piracy, and permanent URL sharing.
    """
    pass
