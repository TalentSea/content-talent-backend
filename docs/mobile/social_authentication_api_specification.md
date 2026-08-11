# Mobile Social & Guest Authentication API Specification (Google OIDC, Facebook OAuth2 & Anonymous Guest Sessions)

This specification defines the industry-standard **OAuth 2.0, OpenID Connect (OIDC), and Anonymous Guest Session** authentication endpoints for mobile applications (iOS & Android / Flutter & React Native).

---

## 🏛️ Architecture Overview

The system uses a **Native SDK Token Exchange & Anonymous Device Session Architecture**.
1. **Registered Subscribers**: The mobile app performs native authentication via Google/Facebook SDKs, obtains cryptographically verifiable identity tokens, and exchanges them with the FastAPI backend for long-lived application sessions.
2. **Anonymous Guests ("Skip Signup")**: When a user taps "Skip Signup", the app generates a unique hardware `device_id` and calls `POST /api/v1/auth/guest` to receive an Anonymous Subscriber Token.
3. **Seamless Account Upgrade**: When a guest later decides to sign in with Google or Facebook, passing their Guest `Authorization: Bearer <guest_access_token>` seamlessly **links and upgrades** their guest account into a permanent subscriber account without losing their Watch History, Watchlist, or Liked Videos!

```
┌────────────────┐          Google / Facebook SDK         ┌────────────────────────┐
│ Mobile App     │ ─────────────────────────────────────► │ Google / Facebook Auth │
│ (iOS/Android)  │ ◄───────────────────────────────────── │ (OIDC / OAuth 2.0)     │
└───────┬────────┘       Returns id_token / access_token  └────────────────────────┘
        │
        │ 1. POST /api/v1/auth/guest    { device_id }       ──► Anonymous Guest Token
        │ 2. POST /api/v1/auth/google   { id_token }        ──► Full Google Token / Upgrade
        │ 3. POST /api/v1/auth/facebook { access_token }    ──► Full Facebook Token / Upgrade
        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                                          │
│ 1. Cryptographically verifies OIDC id_token (Google) or queries Graph API (FB)          │
│ 2. Extracts verified user identity (sub, email, name, avatar_url)                        │
│ 3. Performs User Auto-Provisioning or Account Upgrade in Database                        │
│ 4. Issues Application JWT Access Token (30m) & Refresh Token (60d)                       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints Specification

### 1. `POST /api/v1/auth/guest` — Anonymous Guest Session ("Skip Signup")

Issues an application JWT session for anonymous guest users skipping social login on app launch.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "device_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ef",
  "device_info": "iPhone 15 Pro (iOS 17.4)"
}
```

#### Response Specification (`200 OK`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "guest_def45689a7b8c9d0...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 99,
    "name": "Guest User",
    "email": null,
    "avatar_url": null,
    "provider": "guest",
    "role": "guest",
    "created_at": "2026-08-11T19:00:00Z"
  }
}
```

---

### 2. `POST /api/v1/auth/google` — Sign-In with Google (OIDC) & Account Upgrade

Exchanges a Google OIDC `id_token` for application session JWT tokens.
*(If header `Authorization: Bearer <guest_access_token>` is included, the backend automatically upgrades the existing guest account into a permanent Google subscriber account, preserving watch history and saved videos!)*

#### Request Headers
```http
Authorization: Bearer <guest_access_token>  (Optional: Include if upgrading an active Guest session)
Content-Type: application/json
```

#### Request Body
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
  "device_info": "iPhone 15 Pro (iOS 17.4)"
}
```

#### Response Specification (`200 OK`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "def45689a7b8c9d0...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 99,
    "name": "Jane Doe",
    "email": "jane.doe@gmail.com",
    "avatar_url": "https://lh3.googleusercontent.com/a/AEdFT...",
    "provider": "google",
    "role": "subscriber",
    "created_at": "2026-08-11T19:00:00Z"
  }
}
```

---

### 3. `POST /api/v1/auth/facebook` — Sign-In with Facebook (OAuth 2.0) & Account Upgrade

Exchanges a Facebook OAuth `access_token` for application session JWT tokens.
*(If header `Authorization: Bearer <guest_access_token>` is included, the backend automatically upgrades the existing guest account into a permanent Facebook subscriber account!)*

#### Request Headers
```http
Authorization: Bearer <guest_access_token>  (Optional: Include if upgrading an active Guest session)
Content-Type: application/json
```

#### Request Body
```json
{
  "access_token": "EAABwzLIX58YBA...",
  "device_info": "Samsung Galaxy S24 (Android 14)"
}
```

#### Response Specification (`200 OK`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "abc123456789...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 99,
    "name": "John Smith",
    "email": "john.smith@facebook.com",
    "avatar_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/...",
    "provider": "facebook",
    "role": "subscriber",
    "created_at": "2026-08-11T19:00:00Z"
  }
}
```

---

### 4. `POST /api/v1/auth/refresh` — Silent Access Token Refresh

Generates a fresh short-lived Access Token and rotated Refresh Token when the access token expires.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "refresh_token": "def45689a7b8c9d0..."
}
```

#### Response Specification (`200 OK`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "new_rotated_refresh_token_987...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 99,
    "name": "Jane Doe",
    "email": "jane.doe@gmail.com",
    "avatar_url": "https://lh3.googleusercontent.com/a/AEdFT...",
    "provider": "google",
    "role": "subscriber"
  }
}
```

---

### 5. `POST /api/v1/auth/logout` — Revoke Refresh Token Session

Invalidates the user's active refresh token in the database upon logout.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "refresh_token": "def45689a7b8c9d0..."
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 6. `GET /api/v1/auth/me` — Get Current Authenticated Profile

Retrieves profile metadata for the authenticated mobile subscriber or guest.

#### Request Headers
```http
Authorization: Bearer <access_token>
```

#### Response Specification (`200 OK`)
```json
{
  "id": 99,
  "name": "Jane Doe",
  "email": "jane.doe@gmail.com",
  "avatar_url": "https://lh3.googleusercontent.com/a/AEdFT...",
  "provider": "google",
  "role": "subscriber",
  "created_at": "2026-08-11T19:00:00Z"
}
```

---

## 📱 Mobile App Integration Guidelines

1. **Onboarding Skip Flow**:
   - When user taps **"Skip Signup"**, call `POST /api/v1/auth/guest` with hardware `device_id`.
   - Store the returned `access_token` and `refresh_token` as normal.
2. **Account Upgrade Flow**:
   - When a guest later taps **"Sign in with Google"**, include `Authorization: Bearer <guest_access_token>` in your request to `POST /api/v1/auth/google`.
   - The backend upgrades their account seamlessly—zero data loss!
3. **Token Storage**:
   - Store `access_token` in Mobile Memory / App State.
   - Store `refresh_token` in Hardware Encrypted Vault (`Keychain` for iOS, `Keystore` for Android / `FlutterSecureStorage` / `Expo SecureStore`).
4. **Silent Retry Interceptor**:
   - Catch `HTTP 401 Unauthorized` responses.
   - Automatically issue `POST /api/v1/auth/refresh`.
   - Update in-memory `access_token` and retry original API call without interrupting user flow.

---

## 🧹 Automated 90-Day Guest Cleanup & Data Lifecycle Policy

To prevent database bloat from abandoned guest sessions (users who installed the app, skipped signup, and never returned or deleted the app):

1. **Active Guest Activity Refresh**:
   - Every time an active guest user streams a video or interacts with the app, their database record timestamp (`updated_at`) is automatically refreshed.
2. **Automated Background Garbage Collection**:
   - An automated background worker deletes abandoned guest subscriber records where:
     ```sql
     WHERE provider = 'guest' 
       AND role = 'guest' 
       AND updated_at < NOW() - INTERVAL '90 days'
     ```
   - Because `watch_history`, `video_saves`, and `video_likes` enforce `ON DELETE CASCADE`, associated records for 90-day stale guests are automatically purged.

