---
name: social-and-guest-auth
description: Standards for mobile social authentication (Google OIDC RSA, Facebook Graph API), hardware-bound guest sessions, seamless in-place account upgrading, JWT access/refresh token lifecycles, and automated 90-day stale guest cleanup workers.
---

# Mobile Social & Guest Authentication Subsystem Skill

## Overview
This skill documents authentication architectures, cryptographic identity verification, guest session lifecycles, and subscriber JWT token management for mobile OTT streaming applications.

---

## 1. Hardware-Bound Guest Sessions

To minimize onboarding friction, mobile users can immediately browse without registration:
1. **Device Identification**: The mobile app supplies a unique hardware `device_id`.
2. **Guest Entity**: Created with `role = "guest"`, `provider = "guest"`, and `provider_id = device_id`.
3. **Session Tokens**: Issues standard JWT access tokens with claim `"role": "guest"`.
4. **Access Boundaries**:
   - Guests CAN browse catalog metadata, public playlists, and category feeds.
   - Guests CANNOT stream full video HLS feeds (`POST /views` and `POST /progress` strictly require `role == "subscriber"`).

---

## 2. Seamless In-Place Account Upgrading

When a guest user decides to sign in via Google or Facebook:
* **The In-Place Upgrade Rule**: The existing `Subscriber` record is updated in-place rather than deleted or duplicated:
  ```python
  subscriber.email = verified_email
  subscriber.name = social_profile_name
  subscriber.provider = "google"
  subscriber.provider_id = social_id
  subscriber.role = "subscriber"
  subscriber.save()
  ```
* **Data Retention**: Preserves all historical playback positions in `WatchHistory`, bookmarked videos in `VideoSave`, and liked videos in `VideoLike`.

---

## 3. Cryptographic Token Verification

Third-party social credentials MUST be independently verified against the identity provider's public keys:

### Google OIDC Identity Verification
```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

id_info = id_token.verify_oauth2_token(
    token,
    google_requests.Request(),
    settings.GOOGLE_CLIENT_ID,
)
if id_info["iss"] not in ("accounts.google.com", "https://accounts.google.com"):
    raise HTTPException(status_code=401, detail="INVALID_GOOGLE_ISSUER")

email = id_info["email"]
google_user_id = id_info["sub"]
```

### Facebook Graph Debug API
```python
import requests

app_access_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
url = f"https://graph.facebook.com/debug_token?input_token={access_token}&access_token={app_access_token}"
res = requests.get(url, timeout=10).json()
data = res.get("data", {})

if not data.get("is_valid") or str(data.get("app_id")) != str(settings.FACEBOOK_APP_ID):
    raise HTTPException(status_code=401, detail="INVALID_FACEBOOK_TOKEN")

fb_user_id = data.get("user_id")
```

---

## 4. Token Expiration & Refresh Rotation

* **Access Token**: Short-lived (default: `ACCESS_TOKEN_EXPIRE_MINUTES = 30`), encoded with `JWT_SECRET_KEY` and `JWT_ALGORITHM`.
* **Refresh Token**: Long-lived (default: `REFRESH_TOKEN_EXPIRE_DAYS = 60`), stored in `refresh_tokens` table.
* **Token Rotation**: When exchanging a refresh token, generate a fresh access token and rotate the refresh token to prevent replay vulnerabilities.

---

## 5. Automated Stale Guest Cleanup Worker

To prevent database bloat from abandoned guest sessions:
* **Cascading Purge**: Deletes associated guest watch histories and saves.

---

## 6. Creator Studio Tenant Deactivation Guardrail

In a white-label multi-tenant OTT platform, every subscriber session is bound to a specific creator studio (`sub.tenant_id`). All deactivation checks are centralized in `verify_tenant_active(tenant_or_id)` ([app/utils/auth.py](file:///c:/TECHNICS_TRAINING/WhiteLabeledApp/content-talent-backend/app/utils/auth.py)):

1. **Social & Guest Authentication Gate**: When authenticating (`POST /api/v1/auth/guest`, `/google`, `/facebook`), the service invokes `verify_tenant_active(tenant_id)`. If the studio is suspended, reject immediately with `HTTP 403 Forbidden`.
2. **Session Refresh Gate**: During refresh token exchange (`POST /api/v1/auth/refresh`), invoke `verify_creator_active(subscriber.creator)` before issuing new tokens.
3. **Centralized Dependency Shield**: `get_current_subscriber` in `app/dependencies.py` enforces `verify_creator_active(sub.creator)`. This shields all downstream mobile APIs (streaming, playlists, categories, comments, payments) in one single check without duplicate database lookups.
