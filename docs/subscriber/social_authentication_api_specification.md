# Mobile Social Authentication API Specification (Google OIDC & Facebook OAuth2)

This specification defines the industry-standard **OAuth 2.0 & OpenID Connect (OIDC)** social authentication endpoints for mobile applications (iOS & Android / Flutter & React Native).

---

## 🏛️ Architecture Overview

The system uses a **Native SDK Token Exchange Architecture**. The mobile application performs native authentication via Google/Facebook SDKs, obtains cryptographically verifiable identity tokens, and exchanges them with the FastAPI backend for long-lived application sessions.

```
┌────────────────┐          Google / Facebook SDK         ┌────────────────────────┐
│ Mobile App     │ ─────────────────────────────────────► │ Google / Facebook Auth │
│ (iOS/Android)  │ ◄───────────────────────────────────── │ (OIDC / OAuth 2.0)     │
└───────┬────────┘       Returns id_token / access_token  └────────────────────────┘
        │
        │ POST /api/v1/auth/google   { id_token }
        │ POST /api/v1/auth/facebook { access_token }
        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                                  │
│ 1. Cryptographically verifies OIDC id_token (Google) or queries Graph API (FB)  │
│ 2. Extracts verified user identity (sub, email, name, avatar_url)                │
│ 3. Performs User Auto-Provisioning in Database                                   │
│ 4. Issues Application JWT Access Token (30m) & Refresh Token (60d)               │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints Specification

### 1. `POST /api/v1/auth/google` — Sign-In with Google (OIDC)

Exchanges a Google OIDC `id_token` for application session JWT tokens.

#### Request Headers
```http
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
    "id": 42,
    "name": "Jane Doe",
    "email": "jane.doe@gmail.com",
    "avatar_url": "https://lh3.googleusercontent.com/a/AEdFT...",
    "provider": "google",
    "role": "subscriber",
    "created_at": "2026-08-06T12:00:00Z"
  }
}
```

---

### 2. `POST /api/v1/auth/facebook` — Sign-In with Facebook (OAuth 2.0)

Exchanges a Facebook OAuth `access_token` for application session JWT tokens.

#### Request Headers
```http
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
    "id": 43,
    "name": "John Smith",
    "email": "john.smith@facebook.com",
    "avatar_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/...",
    "provider": "facebook",
    "role": "subscriber",
    "created_at": "2026-08-06T12:00:00Z"
  }
}
```

---

### 3. `POST /api/v1/auth/refresh` — Silent Access Token Refresh

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
    "id": 42,
    "name": "Jane Doe",
    "email": "jane.doe@gmail.com",
    "avatar_url": "https://lh3.googleusercontent.com/a/AEdFT...",
    "provider": "google",
    "role": "subscriber"
  }
}
```

---

### 4. `POST /api/v1/auth/logout` — Revoke Refresh Token Session

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

### 5. `GET /api/v1/auth/me` — Get Current Authenticated Profile

Retrieves profile metadata for the authenticated mobile subscriber.

#### Request Headers
```http
Authorization: Bearer <access_token>
```

#### Response Specification (`200 OK`)
```json
{
  "id": 42,
  "name": "Jane Doe",
  "email": "jane.doe@gmail.com",
  "avatar_url": "https://lh3.googleusercontent.com/a/AEdFT...",
  "provider": "google",
  "role": "subscriber",
  "created_at": "2026-08-06T12:00:00Z"
}
```

---

## 📱 Mobile App Integration Guidelines

1. **Token Storage**:
   - Store `access_token` in Mobile Memory / App State.
   - Store `refresh_token` in Hardware Encrypted Vault (`Keychain` for iOS, `Keystore` for Android / `FlutterSecureStorage` / `Expo SecureStore`).
2. **Silent Retry Interceptor**:
   - Catch `HTTP 401 Unauthorized` responses.
   - Automatically issue `POST /api/v1/auth/refresh`.
   - Update in-memory `access_token` and retry original API call without interrupting user flow.
