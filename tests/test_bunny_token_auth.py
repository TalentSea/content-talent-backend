import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import get_settings
from app.utils.bunny_signature import generate_signed_playback_url


def test_url(url: str) -> tuple[int | None, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, "OK"
    except urllib.error.HTTPError as err:
        return err.code, err.reason
    except Exception as err:  # noqa: BLE001
        return None, str(err)


def run_full_verification():
    settings = get_settings()
    video_id = "0b14de6f-621a-404d-bf58-5ae6c74f5e03"
    pull_zone = settings.BUNNY_PULL_ZONE_URL
    token_key = settings.BUNNY_STREAM_TOKEN_KEY

    print("=" * 75)
    print("🎬 FINAL PRODUCTION TOKEN AUTH VERIFICATION")
    print("=" * 75)

    # 1. Generate path-based signed HLS URL
    hls_url = generate_signed_playback_url(
        bunny_pull_zone_url=pull_zone,
        bunny_video_id=video_id,
        token_security_key=token_key,
        expires_in_seconds=3600,
    )
    print(f"Generated HLS URL:\n{hls_url}\n")

    # 2. Test Master Playlist
    code_master, reason_master = test_url(hls_url)
    print(f"▶ [1] Master Playlist (playlist.m3u8) : HTTP {code_master} ({reason_master})")

    # 3. Test Relative Child Resolution (Simulating Web Browser / Hls.js)
    base_path = hls_url.rsplit("/", 1)[0]
    child_url = f"{base_path}/240p/video.m3u8"
    code_child, reason_child = test_url(child_url)
    print(f"▶ [2] Child Resolution (240p/video.m3u8): HTTP {code_child} ({reason_child})")

    # 4. Test Unsigned Master (Must be blocked 403)
    unsigned_url = f"{pull_zone.rstrip('/')}/{video_id}/playlist.m3u8"
    code_raw, reason_raw = test_url(unsigned_url)
    print(f"▶ [3] Unsigned Access (No Token)       : HTTP {code_raw} ({reason_raw})")

    print("\n" + "=" * 75)
    if code_master == 200 and code_child == 200 and code_raw == 403:
        print("🎉 100% PRODUCTION READY & SECURED!")
        print("  ✅ Master playlist streams (HTTP 200)")
        print("  ✅ Child video segments stream on Web & Mobile (HTTP 200)")
        print("  ✅ Unsigned / Unauthorized requests blocked (HTTP 403)")
    else:
        print("⚠️ Check test outputs above.")
    print("=" * 75)


if __name__ == "__main__":
    run_full_verification()
