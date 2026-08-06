# Mobile Social Authentication API Specification (Google & Facebook OAuth2 / OIDC)

This specification defines the industry-standard **OAuth 2.0 & OpenID Connect (OIDC)** social authentication module for mobile applications (iOS & Android / Flutter & React Native).

---

## 🏛️ Architecture Overview

The system uses a **Native SDK Token Exchange Architecture**. The mobile application performs native authentication via Google/Facebook SDKs, obtains cryptographically verifiable identity tokens, and exchanges them with the FastAPI backend for long-lived application sessions.

```
┌────────────────┐          Google / Facebook SDK         ┌────────────────────────┐
│ Mobile App     │ ─────────────────────────────────────► │ Google / Facebook Auth │
│ (iOS/Android)  │ ◄───────────────────────────────────── │ (OIDC / OAuth 2.0)     │
└───────┬────────┘       Returns id_token / access_token  └────────────────────────┘
        │
        │ POST /api/v1/auth/google  { id_token }
        │ POST /api/v1/auth/facebook { access_token }
        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                                  │
│ 1. Cryptographically verifies OIDC id_token (Google) or queries Graph API (FB)  │
│ 2. Extracts verified user identity (sub, email, name, avatar_url)                │
│ 3. Performs User Auto-Provisioning (Finds or Creates User in SQLite DB)          │
│ 4. Issues Application JWT Access Token (30m) & Refresh Token (60d)               │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schemas

### 1. `User` Entity Extensions (`users` table)
| Field | Type | Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto Increment | Internal user ID |
| `email` | `VARCHAR(255)` | Unique, Indexed, Nullable | Verified user email |
| `name` | `VARCHAR(255)` | Nullable | User display name |
| `avatar_url` | `VARCHAR(500)` | Nullable | Profile picture CDN/remote URL |
| `provider` | `VARCHAR(50)` | Required | Auth provider: `"google"` or `"facebook"` |
| `provider_id` | `VARCHAR(255)` | Required, Indexed | Permanent social provider ID (`google.sub` or `facebook.id`) |
| `role` | `VARCHAR(50)` | Default `"subscriber"` | Role: `"subscriber"`, `"creator"`, `"admin"` |
| `is_active` | `BOOLEAN` | Default `TRUE` | Account status flag |
| `created_at` | `DATETIME` | Default `now()` | Timestamp of account creation |

### 2. `RefreshToken` Entity (`refresh_tokens` table)
| Field | Type | Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto Increment | Token record ID |
| `user` | `FOREIGN KEY` | References `User.id`, `ON DELETE CASCADE` | Linked user account |
| `token_hash` | `VARCHAR(255)` | Unique, Indexed | Hashed SHA-256 string of refresh token |
| `device_info` | `VARCHAR(255)` | Nullable | Client device string (e.g. `"iPhone 15 Pro / iOS 17"`) |
| `expires_at` | `DATETIME` | Indexed | Absolute expiration timestamp (60 days) |
| `is_revoked` | `BOOLEAN` | Default `FALSE` | Revocation status flag |
| `created_at` | `DATETIME` | Default `now()` | Token creation timestamp |

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
    "role": "subscriber"
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
    "role": "subscriber"
  }
}
```

---

### 3. `POST /api/v1/auth/refresh` — Silent Access Token Refresh

Generates a fresh short-lived Access Token using a valid Refresh Token when the access token expires.

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
  "expires_in": 1800
}
```

---

### 4. `POST /api/v1/auth/logout` — Revoke Refresh Token Session

Invalidates the user's active refresh token in the database.

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
  "created_at": "2024-08-01T12:00:00Z"
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
