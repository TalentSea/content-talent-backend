# Administrator & Super Admin — Settings: Profile & Social Links API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints require a valid JWT Bearer token passed in the HTTP request header or via the `admin_access_token` HttpOnly cookie:
```http
Authorization: Bearer <admin_access_token>
```
The administrator identity (`user_id`) is extracted directly from the authenticated session context on the backend (`Depends(get_current_admin)`). No `user_id` parameter is accepted in request bodies or query strings to eliminate Insecure Direct Object Reference (IDOR) risks.

### Multi-Role Support & Scope Matrix
These endpoints serve both **Tenant Administrators** and **Platform Super Admins**:

| Role | `tenant_id` | Profile Attributes (`first_name`, `last_name`, avatar, bio, phone, location) | Social Links (`twitter`, `youtube`, `instagram`) |
| :--- | :---: | :--- | :--- |
| **`super_admin`** | `NULL` | **Identity & Avatar** — Manages name (`first_name`, `last_name`), password, and profile avatar (initially `NULL` upon initial seed; can be added or updated via `POST /photo`). Creator attributes (`bio`, `website`, `phone`, `location`) are strictly `NULL`. | *Not applicable* — Super Admin is not bound to a tenant studio; social links are strictly `NULL`. |
| **`admin` (Owner)** | `> 0` | **Supported** — Updates personal profile attributes and name. | **Supported** — Persisted to Tenant studio branding. |
| **`admin` (Staff)** | `> 0` | **Supported** — Updates personal profile attributes and name. | *Restricted* — Ignored (only studio owners can alter tenant branding links). |

### Architecture Overview
- **Backend Service**: FastAPI (Python) handles authentication, request validation, state management, and profile updates.
- **Database**: Relational Database (Peewee ORM) stores admin profile fields (`first_name`, `last_name`, `email`, `bio`, `website`, `phone`, `location`, `avatar_url`) and social media URLs (`twitter`, `youtube`, `instagram`).
- **Cloud Storage Service**: Bunny Storage API stores and serves profile avatar photos (`assets/avatars/avatar_{user_id}_{timestamp}.{ext}`) via public Storage Pull Zone CDN (`https://talentsea77999.b-cdn.net`).
- **Security Note on Email**: The `email` field returned in `GET /api/v1/admin/profile` is a **read-only identity attribute**. Email and password modifications are strictly handled via the Security Settings flow (`Settings -> Security`) with password re-verification to prevent unauthorized account lockouts.

### Standard HTTP Error Responses
All error responses follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid File Format or File Size Exceeded
```json
{
  "detail": "Unsupported file format. Only JPG and PNG image files under 2MB are allowed."
}
```

#### 2. `401 Unauthorized` — Missing or Expired JWT Token
```json
{
  "detail": "Authentication required: No access token provided"
}
```

#### 3. `404 Not Found` — Administrator Profile Not Found
```json
{
  "detail": "Creator account associated with this session was not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "first_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database Error
```json
{
  "detail": "Internal server error while processing profile request"
}
```

---

## ⚙️ Settings — Profile & Social Links Endpoints

### 1. `GET /api/v1/admin/profile` — Get Profile & Social Settings

Retrieves administrator profile information and social links for rendering the Settings -> Profile UI page.

#### Request Headers
```http
Authorization: Bearer <admin_access_token>
```
*(Or automatic browser `admin_access_token` HttpOnly cookie)*

#### Request Query Parameters — None

#### Response Specification (`200 OK`)

##### Scenario A: Tenant Creator Admin Response
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "owner@acmestudio.com",
  "bio": "Content creator and educator",
  "website": "https://acmestudio.com",
  "phone": "+1 (555) 123-4567",
  "location": "San Francisco, CA",
  "avatar_url": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_101_1785055000.jpg",
  "social_links": {
    "twitter": "https://twitter.com/acmestudio",
    "youtube": "https://youtube.com/@acmestudio",
    "instagram": "https://instagram.com/acmestudio"
  },
  "updated_at": "2024-06-20T10:30:00Z"
}
```

##### Scenario B: Platform Super Admin Response
Per the platform architecture specification, the Platform Super Admin holds authentication and identity attributes (`first_name`, `last_name`, `email`) and their personal `avatar_url`. Creator channel attributes (`bio`, `website`, `phone`, `location`) and studio `social_links` are strictly `null`.

**1. Initial State (Fresh Seed):**
Upon initial database creation, `avatar_url` is `null`:
```json
{
  "first_name": "Murthy",
  "last_name": "Avanithsa",
  "email": "murthyavanithsa@gmail.com",
  "bio": null,
  "website": null,
  "phone": null,
  "location": null,
  "avatar_url": null,
  "social_links": {
    "twitter": null,
    "youtube": null,
    "instagram": null
  },
  "updated_at": "2026-09-25T13:40:00Z"
}
```

**2. Post-Upload State:**
After the Super Admin navigates to their Settings page and uploads/updates their profile picture via `POST /api/v1/admin/profile/photo`, `avatar_url` returns their public CDN image:
```json
{
  "first_name": "Murthy",
  "last_name": "Avanithsa",
  "email": "murthyavanithsa@gmail.com",
  "bio": null,
  "website": null,
  "phone": null,
  "location": null,
  "avatar_url": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_1_1785099000.jpg",
  "social_links": {
    "twitter": null,
    "youtube": null,
    "instagram": null
  },
  "updated_at": "2026-09-25T13:55:00Z"
}
```

---

### 2. `PUT /api/v1/admin/profile` — Update Profile & Name Settings

Updates profile information, name, and optional social links (excluding `email`).

#### Request Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```
*(Or automatic browser `admin_access_token` HttpOnly cookie)*

#### Request Body Specification
All attributes in `ProfileUpdateRequest` are **optional**. The backend applies partial updates—only non-null fields provided in the payload are updated in the database.

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `first_name` | `string` | No | Administrator given name (1-100 characters). Updates `Admin.first_name` and full display name. |
| `last_name` | `string` | No | Administrator family name (1-100 characters). Updates `Admin.last_name` and full display name. |
| `bio` | `string` | No | Biographical statement or role summary. |
| `website` | `string` | No | Personal or studio homepage URL. |
| `phone` | `string` | No | Contact phone number. |
| `location` | `string` | No | Geographic location / office city. |
| `social_links` | `object` | No | Nested social links (`twitter`, `youtube`, `instagram`). Persisted to Tenant branding if caller is tenant owner. |

---

#### Detailed Scenarios

##### Scenario 1: Super Admin Changing Name
When the Platform Super Admin wants to change their display name from "Murthy Avanithsa" to "Murthy Sharma":

**Request:**
```http
PUT /api/v1/admin/profile HTTP/1.1
Authorization: Bearer <super_admin_jwt>
Content-Type: application/json

{
  "first_name": "Murthy",
  "last_name": "Sharma"
}
```

**Database Mutation:**
- Updates `Admin.first_name = 'Murthy'` and `Admin.last_name = 'Sharma'` on the Super Admin's record (`role = 'super_admin'`).
- The computed property `Admin.name` immediately yields `"Murthy Sharma"`.
- Subsequent calls to `GET /api/v1/admin/auth/me` and `GET /api/v1/admin/profile` return the updated name for UI navbar hydration.

**Response (`200 OK`):**
```json
{
  "status": "success"
}
```

##### Scenario 2: Tenant Creator Admin Full Update (Profile + Studio Social Links)
**Request:**
```http
PUT /api/v1/admin/profile HTTP/1.1
Authorization: Bearer <creator_jwt>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Doe",
  "bio": "Lead creator & filmmaker at Acme Studio",
  "website": "https://acmestudio.com",
  "phone": "+1 (555) 123-4567",
  "location": "Los Angeles, CA",
  "social_links": {
    "twitter": "https://twitter.com/acmestudio_new",
    "youtube": "https://youtube.com/@acmestudio",
    "instagram": "https://instagram.com/acmestudio"
  }
}
```

**Response (`200 OK`):**
```json
{
  "status": "success"
}
```

##### Scenario 3: Partial Profile Update (Bio or Phone Only)
**Request:**
```http
PUT /api/v1/admin/profile HTTP/1.1
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "bio": "Updated role description"
}
```

**Response (`200 OK`):**
```json
{
  "status": "success"
}
```

---

### 3. `POST /api/v1/admin/profile/photo` — Upload Avatar Image (Change Avatar)

Uploads a new avatar photo (`JPG` or `PNG`, max 2MB) to Bunny Storage Zone (`assets/avatars/avatar_{admin_id}_{timestamp}.{ext}`) for the authenticated administrator (both Tenant Admins and Platform Super Admins). Replaces any previously uploaded avatar and returns the cache-busting CDN URL.

#### Request Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: multipart/form-data
```
*(Or automatic browser `admin_access_token` HttpOnly cookie)*

#### Request Body (`multipart/form-data`)
- `photo` (File, required): Image file (JPG or PNG, max 2MB).

#### Response Specification (`200 OK`)
```json
{
  "avatar_url": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_1_1785055000.jpg"
}
```

#### Super Admin Settings Page Workflow:
When the Platform Super Admin visits their Settings page (where they can change their password and display name), they can also add or update their profile picture:
1. **Initial State**: Upon initial platform bootstrap via `seed_super_admin()`, `avatar_url` is `null`.
2. **Uploading Profile Picture**: The Super Admin selects an image and submits `POST /api/v1/admin/profile/photo`.
3. **Storage & CDN**: The image binary is stored in Bunny Storage (`assets/avatars/avatar_{admin_id}_{timestamp}.{ext}`) and assigned a cache-busting CDN URL.
4. **Persistence & Instant Rehydration**: The database persists `Admin.avatar_url`. Subsequent calls to `GET /api/v1/admin/auth/me` and `GET /api/v1/admin/profile` immediately reflect the new profile picture across the web portal navbar and settings card.

---

### 4. `POST /api/v1/admin/auth/change-password` — Change Password (Settings -> Security)

Allows administrators (both Tenant Admins and Platform Super Admins) to securely update their account password from the **Settings -> Security** view by re-verifying their current password.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
Content-Type: application/json
```
*(Or automatic browser `admin_access_token` HttpOnly cookie)*

#### Request Body Specification
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

| Field              | Type     | Required | Validation Rules                  | Description                               |
| :----------------- | :------- | :------: | :-------------------------------- | :---------------------------------------- |
| `current_password` | `string` | **Yes**  | Min 1 char                        | Existing account password for verification|
| `new_password`     | `string` | **Yes**  | Min 8 chars, distinct from current| New account password to be hashed         |

#### Error Responses
- `400 Bad Request`: `"Current password does not match"`
- `400 Bad Request`: `"New password cannot be identical to current password"`
- `401 Unauthorized`: `"Authentication required: No access token provided"`

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

