import base64
import hashlib
import hmac
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import get_settings

settings = get_settings()
video_id = "0b14de6f-621a-404d-bf58-5ae6c74f5e03"
pull_zone = settings.BUNNY_PULL_ZONE_URL.rstrip("/")
token_key = settings.BUNNY_STREAM_TOKEN_KEY
expires = int(time.time()) + 3600

# 1. Directory token signing
dir_path = f"/{video_id}/"
message = f"{dir_path}{expires}"
raw_hmac = hmac.new(token_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
b64 = base64.b64encode(raw_hmac).decode("utf-8").replace("+", "-").replace("/", "_").rstrip("=")
token = f"HS256-{b64}"

# Winning URL format
master_url = f"{pull_zone}/bcdn_token={token}&expires={expires}/{video_id}/playlist.m3u8"

print("=" * 75)
print("🎬 VERIFYING FULL STREAMING PIPELINE (MASTER + CHILDS + CHUNKS)")
print("=" * 75)
print(f"Master URL: {master_url}\n")

try:
    req = urllib.request.Request(master_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        print(f"✅ 1. Master Playlist Status: HTTP {resp.status} (OK)")
        content = resp.read().decode("utf-8")
        print("\nMaster Playlist Body:")
        print(content.strip())

        # Test relative resolution stream
        base_path = master_url.rsplit("/", 1)[0]
        child_line = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")][0]
        child_url = f"{base_path}/{child_line}"

        print("\n" + "-" * 75)
        print(f"▶ 2. Testing Resolution Playlist: {child_line}")
        print(f"   URL: {child_url}")

        child_req = urllib.request.Request(child_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(child_req) as child_resp:
            print(f"✅ Child Stream Status: HTTP {child_resp.status} (OK)")
            child_content = child_resp.read().decode("utf-8")
            
            # Find a .ts chunk inside child resolution
            chunk_line = [l.strip() for l in child_content.splitlines() if l.strip() and not l.startswith("#")][0]
            chunk_base_path = child_url.rsplit("/", 1)[0]
            chunk_url = f"{chunk_base_path}/{chunk_line}"

            print("\n" + "-" * 75)
            print(f"▶ 3. Testing Video Chunk (.ts segment): {chunk_line}")
            print(f"   URL: {chunk_url}")

            chunk_req = urllib.request.Request(chunk_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(chunk_req) as chunk_resp:
                chunk_bytes = len(chunk_resp.read())
                print(f"✅ Video Chunk Status: HTTP {chunk_resp.status} (OK - Downloaded {chunk_bytes} bytes)")

        print("\n" + "=" * 75)
        print("🎉 COMPLETE END-TO-END STREAMING VERIFIED!")
        print("  • Master Playlist: 200 OK")
        print("  • Resolution Stream: 200 OK")
        print("  • Video TS Chunks: 200 OK")
        print("=" * 75)

except urllib.error.HTTPError as e:
    print(f"❌ Error: HTTP {e.code} ({e.reason})")
except Exception as e:
    print(f"❌ Error: {e}")



