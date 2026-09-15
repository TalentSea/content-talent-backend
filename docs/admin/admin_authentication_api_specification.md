# Creator Admin Authentication & Identity Lifecycle API Specification

This specification defines the complete authentication, credential management, token lifecycle, and account provisioning architecture for the **Creator Admin Web Portal** (`/api/v1/admin/auth/*`).

---

## 1. System Architecture & Design Principles

### 1.1 Multi-Tenant B2B SaaS Provisioning

The platform operates as a specialized **White-Labeled Creator OTT Platform**. Unlike public consumer applications, the Creator Admin Studio is strictly accessible to verified, paying creators onboarded by platform operators.

- **Zero Public Registration (`/register`)**: There is intentionally **NO public sign-up endpoint** on the Creator Admin portal. Public visitors cannot create admin accounts.
- **Controlled Account Provisioning**: Creator accounts, studio spaces, default branding themes, and subscription plans are provisioned atomically by platform administrators via an internal CLI utility (`app.scripts.create_creator`) or secure provider orchestration.
- **Attack Surface Elimination**: Removing public registration eliminates bot account spam, credential stuffing, orphaned tenant database records, and unauthorized dashboard access attempts.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PLATFORM OPERATOR / CLI PROVISIONING                                                                             │
│ python -m app.scripts.create_creator --email creator@studio.com --password "Secret123!" --studio-name "Studio"  │
└────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────┘
                                                         │
                                        Atomic Database Transaction
                                                         │
                        ┌────────────────────────────────┼────────────────────────────────┐
                        ▼                                ▼                                ▼
               ┌─────────────────┐              ┌─────────────────┐              ┌────────────────┐
               │  Admin Record   │              │ Branding Record │              │ 2 Fixed Plans  │
               │ (Hashed Pwd)    │              │(Studio Identity)│              │with_ads & no_ads│
               └────────┬────────┘              └─────────────────┘              └────────────────┘
                        │
                        │ Login Credentials Delivered via Secure Channel (Email / SMS)
                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ CREATOR ADMIN WEB PORTAL (React / Vite SPA)                                                                      │
│ 1. POST /api/v1/admin/auth/login   ──► Receives Access Token (30m) & HttpOnly Refresh Cookie (60d)│
│ 2. GET  /api/v1/admin/auth/me      ──► Rehydrates profile & verifies active token                                │
│ 3. POST /api/v1/admin/auth/refresh ──► Silently renews expired access token                                      │
│ 4. POST /api/v1/admin/auth/logout  ──► Server-side revocation of refresh session                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Dual-Token Session Security Standard & Theft Mitigation

To eliminate session compromise and Cross-Site Scripting (XSS) risks, the system enforces an industry-standard **In-Memory Access Token + HttpOnly Cookie Refresh Token** architecture:

| Token Type | Lifespan | Transport / Storage Medium | Security & Theft Protection |
| :--- | :--- | :--- | :--- |
| **Access Token** | **30 Minutes** | In-Memory (React State / Closure) & HTTP `Authorization: Bearer <token>` | Never written to `localStorage`. Short lifespan limits stolen token window. Cryptographically signed JWT (`HS256`). |
| **Refresh Token** | **60 Days** | **`HttpOnly; Secure; SameSite=Strict` Cookie** | **Completely inaccessible to JavaScript / XSS**. Stored in DB strictly as a **SHA-256 one-way hash**. Restricted to path `/api/v1/admin/auth`. |

#### How We Prevent & Handle Refresh Token Compromise:

1. **XSS Immunity via `HttpOnly` Cookie**:
   - Storing refresh tokens in `localStorage` makes them vulnerable to malicious scripts or vulnerable npm dependencies.
   - By transmitting the refresh token inside an **`HttpOnly` Cookie**, browser JavaScript cannot read `document.cookie`. Even if an attacker executes arbitrary JavaScript on the page, the refresh token **cannot be stolen or exfiltrated**.

2. **CSRF Protection via `SameSite=Strict`**:
   - The cookie is marked `SameSite=Strict` and scoped strictly to `Path=/api/v1/admin/auth`. Cross-origin websites cannot trigger token refresh requests on behalf of the creator.

3. **Single-Use Refresh Token Rotation (RTR)**:
   - Every time `POST /api/v1/admin/auth/refresh` is called, the used refresh token is **immediately invalidated (burned)** and replaced with a newly minted one.

4. **Single Active Session & Multi-Device Isolation**:
   - Because `admins.refresh_token` is stored as a single column on the `admins` table, each creator account maintains **one active refresh session at a time**.
   - When an admin logs in on a newer device (Device B), Device B's new refresh token hash overwrites `admins.refresh_token`.
   - **Non-Destructive Mismatch Handling (Clean Multi-Device Experience)**:
     - When Device A (previously closed without explicit logout) reopens and attempts a silent token refresh (`POST /api/v1/admin/auth/refresh`), its incoming cookie hash will not match the newly stored hash for Device B.
     - The backend returns `401 Unauthorized` with detail: `"Session expired or active on another device; please re-login"`.
     - **Crucial Rule**: The server **DOES NOT set `admins.refresh_token = NULL`**.
     - **Result**: Device B's active session remains completely intact and undisturbed. Device A's frontend cleanly intercepts the 401 and redirects the user to `/login`. Device A's stale request never inadvertently logs out Device B.

5. **Instant Server-Side Revocation (`POST /logout`)**:
   - Calling `POST /api/v1/admin/auth/logout` explicitly sets `admins.refresh_token = NULL` in the database and clears the browser cookie (`Max-Age=0`), terminating the active session immediately.

---

### 1.3 Strict IDOR Security & Context Extraction

- No `user_id` or `admin_id` parameter is accepted in request bodies or query parameters across any admin route.
- The authenticated creator identity (`user_id`) is extracted strictly from the validated JWT token claims on the backend via the FastAPI dependency:
  ```python
  admin_ctx = Depends(get_current_admin)
  # admin_ctx["user_id"] -> securely isolates all studio operations
  ```
- Any attempt by an ordinary mobile app subscriber to present a subscriber token to an admin route results in an immediate `403 Forbidden` response.

---

## 2. Cryptographic & Database Standards

### 2.1 Password Storage: PBKDF2-HMAC-SHA256

Passwords are NEVER stored in plaintext. Passwords are stored in the `Admin.password_hash` column using standard library `hashlib.pbkdf2_hmac` with the following parameters (NIST SP 800-132 compliant):

- **Algorithm**: `PBKDF2-HMAC-SHA256`
- **Iterations**: `600,000`
- **Salt**: 16 bytes of cryptographically secure random bytes generated via `secrets.token_bytes(16)`
- **Stored Format**: `pbkdf2_sha256$600000$<salt_hex>$<hash_hex>`
- **Comparison**: Constant-time string comparison using `secrets.compare_digest` to prevent timing attacks.

### 2.2 Refresh Token Hashing

Raw refresh tokens are sent only to the authenticated client. The backend stores:
$$\text{refresh\_token\_hash} = \text{SHA-256}(\text{raw\_refresh\_token})$$
If the database is read or dumped, attackers cannot use the stored hash values to generate valid sessions.

### 2.3 Updated `admins` Database Table Schema

```sql
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NULL,
    first_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NULL,
    phone VARCHAR(50) NULL,
    location VARCHAR(255) NULL,
    bio TEXT NULL,
    website VARCHAR(255) NULL,
    avatar_url VARCHAR(500) NULL,
    twitter_url VARCHAR(255) NULL,
    youtube_url VARCHAR(255) NULL,
    instagram_url VARCHAR(255) NULL,
    refresh_token TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_admins_email ON admins(email);
```

---

## 3. Standard HTTP Error Responses

All error responses across all admin authentication endpoints adhere to the unified FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Missing or Invalid Payload

```json
{
  "detail": "Email and password are required"
}
```

#### 2. `401 Unauthorized` — Invalid Credentials, Expired Token, or Active on Another Device

```json
{
  "detail": "Invalid email or password"
}
```

_When token has expired:_

```json
{
  "detail": "Authentication token has expired"
}
```

_When refresh token was superseded by a newer device login:_

```json
{
  "detail": "Session expired or active on another device; please re-login"
}
```

#### 3. `403 Forbidden` — Insufficient Privileges (Non-Admin Token)

```json
{
  "detail": "Admin portal authorization required"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database / Server Failure

```json
{
  "detail": "Internal server error during authentication"
}
```

---

## 4. API Endpoints Specification

Base Route Prefix:

```http
/api/v1/admin/auth
```

---

### 4.1 `POST /api/v1/admin/auth/login` — Creator Admin Login

Authenticates a creator with their registered email and password, returning a short-lived access token, a long-lived refresh token, and a summary profile for dashboard hydration.

#### Request Headers

```http
Content-Type: application/json
```

#### Request Body

```json
{
  "email": "creator@example.com",
  "password": "SecurePassword123!"
}
```

#### Request Validation Rules

- `email`: String, required, valid email format, automatically trimmed and lowercased.
- `password`: String, required, minimum 8 characters.

#### Response Headers
```http
Set-Cookie: admin_refresh_token=a4f8902c3e451b67d890123456789abcdef0123456789abcdef0123456789abc; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/admin/auth; Max-Age=5184000
```

#### Response Specification (`200 OK`)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJDcmVhdG9yIEFkbWluIiwiZXhwIjoxNzk4NTMwMDAwfQ.abcdef...",
  "token_type": "bearer",
  "expires_in": 1800,
  "admin": {
    "id": 1,
    "email": "creator@example.com",
    "first_name": "Creator",
    "last_name": "Admin",
    "studio_name": "Creator OTT Studio",
    "avatar_url": "https://talent-sea987.b-cdn.net/assets/avatars/avatar_1_1785055000.jpg"
  }
}
```

#### Response Fields:

- `access_token` (string): Signed JWT valid for 30 minutes (`1800` seconds), kept strictly in-memory by the frontend client.
- `token_type` (string): Fixed value `"bearer"`.
- `expires_in` (integer): Access token lifespan in seconds (`1800` seconds = 30 minutes).
- `admin` (object): Core creator identity attributes for rendering the dashboard header without secondary network requests.
  - `id` (integer): Unique creator admin ID.
  - `email` (string): Account login email.
  - `first_name` (string): Creator's first name.
  - `last_name` (string): Creator's last name.
  - `studio_name` (string): Public channel / OTT studio brand name.
  - `avatar_url` (string | null): CDN URL to profile photo asset.

*(Note: The 60-day `refresh_token` is transmitted strictly via the secure `Set-Cookie` response header and is never exposed in the JSON payload, ensuring complete protection against JavaScript-based token exfiltration).*

---

### 4.2 `POST /api/v1/admin/auth/refresh` — Silent Token Refresh

Exchanges a valid 60-day refresh token for a newly minted 30-minute access token. Performs automatic single-use token rotation while preserving active sessions on newer devices during concurrent device switches.

#### Request Headers

```http
Cookie: admin_refresh_token=<token_from_httponly_cookie>
```
*(No request body is needed; the browser automatically transmits the HttpOnly cookie with `withCredentials: true`).*

#### Processing Logic & Multi-Device Handling:

1. **Token Extraction**: Reads `admin_refresh_token` from incoming `HttpOnly` Cookie. If missing, returns `401 Unauthorized` (`"Refresh token missing"`).
2. **Hash & Verification**: Hashes incoming token with SHA-256 and queries the `admins` table.
3. **Session Matching & Non-Destructive Invalidation**:
   - If `admins.refresh_token` does not match the incoming token hash (e.g., the creator logged in on another device or the session was rotated):
     - The server returns `401 Unauthorized` with `{"detail": "Session expired or active on another device; please re-login"}`.
     - **IMPORTANT**: The server **DOES NOT wipe `admins.refresh_token` in the database**. Leaving the current database hash intact ensures the active device (Device B) remains logged in, while the stale device (Device A) is cleanly prompted to re-login.
4. **Token Rotation**: If the hash matches:
   - Generates a new 30-minute access token and a brand-new 60-day refresh token.
   - Burns the old token in the database by updating `admins.refresh_token = SHA-256(new_refresh_token)`.
5. **Cookie Update**: Emits a fresh `Set-Cookie` header with the rotated refresh token (`Max-Age=5184000`).

#### Response Headers
```http
Set-Cookie: admin_refresh_token=b5e9013d4f562c78e90123456789abcdef0123456789abcdef0123456789def; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/admin/auth; Max-Age=5184000
```

#### Response Specification (`200 OK`)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJDcmVhdG9yIEFkbWluIiwiZXhwIjoxNzk4NTMxODAwfQ.xyz...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### 4.3 `GET /api/v1/admin/auth/me` — Session Identity & Rehydration

Retrieves the current authenticated creator's core session identity and studio branding status. Used by the Web Admin SPA on page load, browser refresh (F5), or route changes to repopulate global navbar/layout state and verify that the stored access token remains active and valid.

#### Request Headers

```http
Authorization: Bearer <admin_access_token>
```

#### Processing Logic:

1. Validates the JWT Bearer token and verifies `role == "admin"` using `get_current_admin`.
2. Reads the creator record from the `admins` table.
3. Retrieves the associated `branding` studio name.
4. Returns the lean `AdminSummaryResponse` (exactly matching the `admin` object returned upon login).

#### Response Specification (`200 OK`)

```json
{
  "id": 1,
  "email": "creator@example.com",
  "first_name": "Creator",
  "last_name": "Admin",
  "studio_name": "Creator OTT Studio",
  "avatar_url": "https://talent-sea987.b-cdn.net/assets/avatars/avatar_1_1785055000.jpg"
}
```

#### Response Fields:

- `id` (integer): Unique creator admin ID.
- `email` (string): Account login email.
- `first_name` (string | null): Creator's first name.
- `last_name` (string | null): Creator's last name.
- `studio_name` (string | null): Public channel / OTT studio brand name.
- `avatar_url` (string | null): CDN URL to profile photo asset.

*(Note: Heavy form-editing fields such as `bio`, `website`, `phone`, `location`, and `social_links` are decoupled from global session rehydration and served strictly by `GET /api/v1/admin/profile` when loading the Settings ➔ Profile edit screen).*

#### Why `/api/v1/admin/auth/me` is Essential:

1. **SPA Page Refresh & Perfect Symmetry**: When a creator refreshes the page (F5), client-side memory is wiped. The frontend calls `/me` with the access token, receiving the exact same `AdminSummaryResponse` structure as returned on `/login`.
2. **Route Guarding**: If the token has expired, `/me` returns `401 Unauthorized`, prompting the frontend to trigger a silent cookie refresh (`POST /refresh`) or redirect to the login page.
3. **Zero Redundancy**: Layout and header components receive only the identity metadata they need to render, eliminating payload bloat on every page reload.

---

### 4.4 `POST /api/v1/admin/auth/logout` — Revoke Refresh Session

Invalidates the active session on the backend by erasing the stored refresh token hash in the database and clearing the browser cookie.

#### Request Headers

```http
Authorization: Bearer <admin_access_token>
```
*(No request body is needed; the browser automatically transmits the HttpOnly cookie, and the caller is authenticated via the Bearer token).*

#### Processing Logic:

1. Resolves caller's `user_id` via `get_current_admin`.
2. Updates `admins` table setting `refresh_token = NULL` for this creator.
3. Clears the browser's `admin_refresh_token` cookie by sending `Set-Cookie` with `Max-Age=0`.
4. Any subsequent calls to `POST /api/v1/admin/auth/refresh` will immediately fail.

#### Response Headers
```http
Set-Cookie: admin_refresh_token=; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/admin/auth; Max-Age=0
```

#### Response Specification (`200 OK`)

```json
{
  "message": "Successfully logged out"
}
```

---

## 5. Creator Provisioning CLI Specification

Since there is **NO public registration**, platform operators provision new creator accounts via a secure internal CLI script (`app.scripts.create_creator`).

### 5.1 CLI Command Syntax & Options

The command accepts command-line flags or prompts interactively for sensitive fields:

```bash
# Option A: Direct execution with command-line flags:
python -m app.scripts.create_creator \
    --email creator@example.com \
    --password "SuperSecretPass123!" \
    --first-name "John" \
    --last-name "Doe" \
    --studio-name "John Doe Studio"

# Option B: Secure interactive execution (password hidden without terminal echo):
python -m app.scripts.create_creator --email creator@example.com --studio-name "John Doe Studio"
# Prompt: Enter creator password (min 8 chars): [hidden]
# Prompt: Confirm creator password: [hidden]
```

#### CLI Options Reference

| Argument | Type | Required | Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `--email` | String | **YES** | None | Creator's primary login email. Case-insensitive, automatically trimmed. |
| `--password` | String | **YES** | Interactive Prompt | Initial login password (minimum 8 characters). If omitted from the command line, prompts interactively using `getpass` to avoid logging secrets in terminal history. |
| `--first-name` | String | NO | `None` | Creator's first name. |
| `--last-name` | String | NO | `None` | Creator's last name. |
| `--studio-name` | String | NO | `f"{first_name} {last_name} Studio"` or `"Creator Studio"` | Public channel / OTT studio brand name. |

---

### 5.2 Atomic Provisioning Steps (Complete Eager Provisioning)

To maintain strict tenant data consistency in a B2B SaaS environment, every newly onboarded creator is **100% fully initialized** in an **atomic database transaction**:

1. **Email Conflict Verification**: Checks `Admin.get_or_none(Admin.email == email)`. If an account already exists, execution aborts with `Error: Admin with email <email> already exists`.
2. **Password Validation & Hashing**:
   - Validates that the password length is at least 8 characters.
   - Generates 16 bytes of cryptographically secure random salt via `secrets.token_bytes(16)`.
   - Hashes password using NIST SP 800-132 compliant `PBKDF2-HMAC-SHA256` with 600,000 iterations.
   - Output string: `pbkdf2_sha256$600000$<salt_hex>$<hash_hex>`.
3. **Admin User Creation**: Inserts new row into `admins` table:
   - `email`: `creator@example.com`
   - `password_hash`: `<pbkdf2_hash>`
   - `first_name`: `"John"`
   - `last_name`: `"Doe"`
4. **Branding Studio Provisioning (Eager 1:1 Invariant)**: Inserts the studio identity record into `branding` table linked to `user_id`:
   - `user_id`: `admin.id` (Foreign key to `admins.id`)
   - `studio_name`: Provided `--studio-name` (or defaults to `f"{first_name} {last_name} Studio"` / `"Creator Studio"`)
   - `tagline`: `NULL` (creator fills this in via Admin Studio UI)
   - `description`: `NULL` (creator fills this in via Admin Studio UI)
   - `banner_url`: `NULL` (uploaded later via `POST /api/v1/admin/branding/banner`)
   - `logo_url`: `NULL` (uploaded later via `POST /api/v1/admin/branding/logo`)
5. **Atomic 2-Plan Provisioning**: Inserts the **two mandatory subscription tiers** linked to `user_id`:
   - **Plan 1 (`plan_type = "with_ads"`)**:
     - `name`: `"Standard with Ads"`
     - `description`: `"Access to our full catalog with occasional commercial breaks."`
     - `base_price`: `99.0` (₹99/month)
     - `billing_period_value`: `1`
     - `billing_period_unit`: `"months"`
   - **Plan 2 (`plan_type = "no_ads"`)**:
     - `name`: `"Premium Ad-Free"`
     - `description`: `"Unlimited streaming with zero ads and maximum quality."`
     - `base_price`: `199.0` (₹199/month)
     - `billing_period_value`: `1`
     - `billing_period_unit`: `"months"`

#### Why Eager Provisioning is the Professional Standard for this Platform:
* **Guaranteed 1:1 Relationship**: An Admin *is* a Creator Studio. A creator never exists in a "half-born" or orphaned state.
* **Immediate Mobile App Readiness**: When a mobile subscriber app connects using this `creator_id`, `GET /api/v1/branding` immediately returns the valid studio name instead of `null` or a 404 error.
* **Query Performance & Cleanliness**: All internal services, analytics pipelines, and reporting scripts can reliably `INNER JOIN` `admins` and `branding` without defensive `LEFT JOIN`s or null-coalescing workarounds.

Once completed, the operator delivers the login credentials to the creator, and the creator logs into the Admin Studio.

---

## 6. Frontend Integration Architecture (React / Vite SPA)

### 6.1 State Management & Interceptor Architecture

The web application uses an Axios HTTP interceptor with `withCredentials: true` to handle transparent token renewal without ever exposing the refresh token to JavaScript:

```
                  ┌───────────────────────────────────┐
                  │ Creator Performs Dashboard Action │
                  └─────────────────┬─────────────────┘
                                    │
                                    ▼
                      HTTP Request with Access Token
                                    │
                  ┌─────────────────┴─────────────────┐
                  │ Backend Returns Status Code       │
                  └─────────────────┬─────────────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
             Status == 200                     Status == 401
                   │                       (Access Token Expired)
                   ▼                                 │
           Return Data to UI                         ▼
                                         Call POST /auth/refresh
                                         (Browser sends HttpOnly Cookie)
                                                     │
                                        ┌────────────┴────────────┐
                                        │                         │
                                  Success (New Token)        Failure (Revoked)
                                        │                         │
                                        ▼                         ▼
                               Update In-Memory Token     Redirect to /login
                               & Replay Failed Request
```

### 6.2 Implementation Reference (Axios Interceptor with HttpOnly Cookies)

```javascript
import axios from "axios";

// 1. In-memory access token storage (immune to localStorage XSS exfiltration)
let inMemoryAccessToken = null;

export const setAccessToken = (token) => {
  inMemoryAccessToken = token;
};

export const getAccessToken = () => inMemoryAccessToken;

const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true, // Guarantees HttpOnly refresh_token cookie is sent on cross-origin requests
});

// 2. Attach short-lived Access Token to every outgoing request
api.interceptors.request.use((config) => {
  if (inMemoryAccessToken) {
    config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
  }
  return config;
});

// 3. Intercept 401 Unauthorized responses & silently refresh via HttpOnly cookie
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Browser automatically attaches HttpOnly 'admin_refresh_token' cookie
        const { data } = await axios.post(
          "/api/v1/admin/auth/refresh",
          {},
          { withCredentials: true }
        );

        // Update in-memory access token
        setAccessToken(data.access_token);

        // Re-attach new token and replay original request
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token expired or revoked -> redirect to login
        setAccessToken(null);
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 7. Sequence Diagrams

### 7.1 Admin Login & Silent Refresh Flow

```mermaid
sequenceDiagram
    autonumber
    actor Creator as Creator (Browser)
    participant SPA as Web Admin Portal (React)
    participant API as FastAPI Backend (/api/v1/admin/auth)
    participant DB as PostgreSQL / SQLite Database

    Note over Creator,API: Step 1: Creator Login
    Creator->>SPA: Enters email & password
    SPA->>API: POST /login { email, password }
    API->>DB: Query Admin by email
    DB-->>API: Returns Admin record + password_hash
    API->>API: Verify PBKDF2 password match
    API->>API: Generate Access Token (30m) & Refresh Token (60d)
    API->>DB: Store SHA-256(refresh_token) in admins.refresh_token
    API-->>SPA: Set-Cookie: admin_refresh_token (HttpOnly) & 200 OK { access_token, admin }
    SPA->>Creator: Display Admin Dashboard

    Note over Creator,API: Step 2: 30 Minutes Later (Access Token Expired)
    Creator->>SPA: Navigates to Videos page
    SPA->>API: GET /api/v1/admin/videos (Expired Access Token)
    API-->>SPA: 401 Unauthorized ("Authentication token has expired")

    Note over SPA,API: Step 3: Silent Token Refresh (Axios Interceptor)
    SPA->>API: POST /refresh (Browser automatically sends HttpOnly Cookie)
    API->>DB: Query Admin by SHA-256(refresh_token)
    DB-->>API: Returns matching Admin
    API->>API: Generate New Access Token (30m) & Rotated Refresh Token
    API->>DB: Update admins.refresh_token = SHA-256(new_refresh_token)
    API-->>SPA: Set-Cookie: new_refresh_token (HttpOnly) & 200 OK { access_token }
    SPA->>API: Replay GET /api/v1/admin/videos with new Access Token
    API-->>SPA: 200 OK (Video List Data)
    SPA->>Creator: Display Videos seamlessly without interruption
```

---

### 7.2 Session Rehydration (`GET /me`) on Page Reload (F5)

```mermaid
sequenceDiagram
    autonumber
    actor Creator as Creator (Browser)
    participant SPA as Web Admin Portal (React)
    participant API as FastAPI Backend (/api/v1/admin/auth)
    participant DB as PostgreSQL / SQLite Database

    Creator->>SPA: Hits browser refresh (F5)
    SPA->>API: POST /api/v1/admin/auth/refresh (Browser sends HttpOnly Cookie)
    API-->>SPA: 200 OK { access_token } (Refreshes in-memory session)
    SPA->>API: GET /api/v1/admin/auth/me (Authorization: Bearer <token>)
    API->>API: Validate JWT signature & claims (get_current_admin)
    API->>DB: Fetch fresh Admin profile & studio metadata
    DB-->>API: Returns Admin + Studio info
    API-->>SPA: 200 OK { id, email, first_name, last_name, studio }
    SPA->>SPA: Hydrate user state & studio branding
    SPA->>Creator: Render authenticated dashboard
```

---

## 8. Summary Checklist of Next Implementation Steps

| Step | Component                      | Action Required                                                                                                | Status    |
| :--- | :----------------------------- | :------------------------------------------------------------------------------------------------------------- | :-------- |
| 1    | **Database Model**             | Add `password_hash = CharField(max_length=255, null=True)` to `app/models/admin.py`                            | Pending   |
| 2    | **Security Utils**             | Implement `hash_password(password)` and `verify_password(plain, hashed)` in `app/utils/auth.py`                | Pending   |
| 3    | **Provisioning CLI**           | Implement `app/scripts/create_creator.py` (atomic creation of Admin with hashed password + Branding + 2 Plans) | Pending   |
| 4    | **Pydantic Schemas**           | Create `app/schemas/admin/auth_schemas.py` (`AdminLoginRequest`, `AdminTokenResponse`, `AdminProfileResponse`) | Pending   |
| 5    | **Auth Routes**                | Implement `app/routes/admin/auth_routes.py` (`/login`, `/refresh`, `/me`, `/logout`)                           | Pending   |
| 6    | **Main Router**                | Register `auth_routes` in `app/main.py` under prefix `/api/v1/admin/auth`                                      | Pending   |
| 7    | **Two-Tier Plans Refactoring** | Refactor `SubscriptionPlan` model, service, and routes to strictly support `"with_ads"` and `"no_ads"`         | Next Task |
