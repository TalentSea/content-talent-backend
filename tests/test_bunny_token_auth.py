import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import get_settings
from app.utils.bunny_signature import (
    generate_signed_playback_url,
)


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


def run_production_signature_test():
    settings = get_settings()
    video_id = "0b14de6f-621a-404d-bf58-5ae6c74f5e03"
    pull_zone = settings.BUNNY_PULL_ZONE_URL
    token_key = settings.BUNNY_STREAM_TOKEN_KEY

    print("=" * 70)
    print("🎬 TESTING PRODUCTION BUNNY SIGNATURE ENGINE")
    print(f"Video ID      : {video_id}")
    print(f"Pull Zone URL : {pull_zone}")
    print("=" * 70)

    # 1. Test Valid HLS Signed URL
    hls_url = generate_signed_playback_url(
        bunny_pull_zone_url=pull_zone,
        bunny_video_id=video_id,
        token_security_key=token_key,
        expires_in_seconds=3600,
    )
    code_hls, reason_hls = test_url(hls_url)
    print(f"\n▶ [1] Signed HLS URL Test       : HTTP {code_hls} ({reason_hls})")
    print(f"    URL: {hls_url}")

    # 2. Test Unsigned HLS URL (Should be 403 Forbidden)
    unsigned_url = f"{pull_zone.rstrip('/')}/{video_id}/playlist.m3u8"
    code_raw, reason_raw = test_url(unsigned_url)
    print(f"\n▶ [2] Unsigned HLS URL Test     : HTTP {code_raw} ({reason_raw})")
    print(f"    URL: {unsigned_url}")

    print("\n" + "=" * 70)
    if code_hls == 200 and code_raw == 403:
        print("🎉 ALL TESTS PASSED! 100% SECURE & WORKING!")
        print("  • Legitimate token requests: HTTP 200 (Accessible)")
        print("  • Unauthorized / Unsigned requests: HTTP 403 (Blocked)")
    else:
        print("⚠️ Check test outputs above.")
    print("=" * 70)


if __name__ == "__main__":
    run_production_signature_test()
