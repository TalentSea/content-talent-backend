# Mobile Social & Guest Authentication API Specification (Google OIDC, Facebook OAuth2 & Anonymous Guest Sessions)

This specification defines the industry-standard **OAuth 2.0, OpenID Connect (OIDC), and Anonymous Guest Session** authentication endpoints for mobile applications (iOS & Android / Flutter & React Native).

---

## 🏛️ Architecture Overview

The system uses a **Native SDK Token Exchange & Anonymous Device Session Architecture** with mandatory **Multi-Tenant Creator Isolation**:
1. **Registered Subscribers**: The mobile app performs native authentication via Google/Facebook SDKs, obtains cryptographically verifiable identity tokens, and exchanges them with the FastAPI backend for long-lived application sessions bound to a specific Admin Creator (`creator_id`).
2. **Anonymous Guests ("Skip Signup")**: When a user taps "Skip Signup", the app generates a unique hardware `device_id` and calls `POST /api/v1/auth/guest` with `creator_id` to receive an Anonymous Subscriber Token.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Mobile Application                                                                       │
│ 1. Taps "Skip Signup" OR Signs in via Native Google / Facebook SDK                       │
│ 2. Sends Auth Request to Backend with mandatory creator_id                               │
│         │                                                                                │
│         │ 1. POST /api/v1/auth/guest    { creator_id, device_id }   ──► Guest Token      │
│         │ 2. POST /api/v1/auth/google   { creator_id, id_token }    ──► Google Token     │
│         │ 3. POST /api/v1/auth/facebook { creator_id, access_token} ──► Facebook Token   │
│         ▼                                                                                │
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                                          │
│ 1. Cryptographically verifies OIDC id_token (Google) or queries Graph API (FB)          │
│ 2. Extracts verified user identity (sub, email, name, avatar_url)                        │
│ 3. Performs User Auto-Provisioning bound to creator_id in Database                        │
│ 4. Issues Application JWT Access Token containing user_id & creator_id                   │
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
  "creator_id": 1,
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
  "creator_id": 1,
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
  "creator_id": 1,
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
    "id": 100,
    "name": "John Smith",
    "email": "john.smith@facebook.com",
    "avatar_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/...",
    "provider": "facebook",
    "role": "subscriber",
    "created_at": "2026-08-11T19:30:00Z"
  }
}
```

---

### 4. `POST /api/v1/auth/refresh` — Refresh Access Token

Rotates a 60-day Refresh Token to issue a fresh 30-minute Access Token.

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
  "refresh_token": "new_def45689a7b8c9d0...",
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

### 5. `POST /api/v1/auth/logout` — Revoke Session

Revokes the refresh token and terminates the subscriber's session.

#### Request Headers
```http
Authorization: Bearer <access_token>
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
  "success": true,
  "message": "Session terminated successfully"
}
```

---

### 6. `GET /api/v1/auth/me` — Get Subscriber Profile

Returns current subscriber identity details.

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
