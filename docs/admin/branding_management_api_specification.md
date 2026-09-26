# Creator Admin — Branding & Customization API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints in this specification require a valid JWT Bearer access token passed in the HTTP request header:
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
```
Identity and tenant context are strictly derived from the validated JWT token context (`get_current_admin`). Under no circumstances is `tenant_id` or `user_id` accepted as an HTTP query parameter or request body parameter, eliminating Insecure Direct Object Reference (IDOR) vulnerabilities. For Platform Super Admins, the active tenant context can be selected via the `X-Tenant-Id` header (falling back to the first active tenant if omitted).

### Architecture Overview
- **Domain Purpose**: Manages the public-facing **Creator Identity & White-Label OTT App Branding** (Studio Name, Tagline, Description, Hero Banner, and Studio Logo). This is distinct from personal admin account settings (`Settings -> Profile`).
- **Backend Service**: FastAPI (Python) handles authentication, schema validation, state management, and file upload processing.
- **Database**: Relational Database (Peewee ORM) stores branding attributes directly on the `Tenant` entity (`name` as `studio_name`, `tagline`, `description`, `banner_url`, `logo_url`, `updated_at`). This unified design eliminates the redundant 1:1 `branding` table while preserving complete backward compatibility for frontends.
- **Cloud Storage Service**: Bunny Storage API stores and serves uploaded branding assets (`assets/branding/logo_tenant_{tenant_id}_{timestamp}.{ext}`, `assets/branding/banner_tenant_{tenant_id}_{timestamp}.{ext}`) via public Storage Pull Zone CDN (`https://talentsea77999.b-cdn.net`).

---

### Standard HTTP Error Responses
All error responses follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid File Format or Upload Failure
```json
{
  "detail": "Unsupported file format. Only PNG, SVG, JPG, and WebP image files under 5MB are allowed."
}
```

#### 2. `401 Unauthorized` — Missing or Expired JWT Token
```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `404 Not Found` — Branding Record Not Found
```json
{
  "detail": "Creator branding configuration not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "studio_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database or Storage Failure
```json
{
  "detail": "Internal server error while processing branding request"
}
```

---

## 🎨 Branding & Customization Endpoints

### 1. `GET /api/v1/admin/branding` — Fetch Creator Branding Identity & Assets

Retrieves current creator brand identity details, tagline, description, banner, and logo for rendering the **Branding & Customization** UI page.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
```

#### Request Query Parameters — None

#### Response Specification (`200 OK`)
```json
{
  "studio_name": "Creator Academy",
  "tagline": "Learn from industry leaders",
  "description": "Your premier portal for high-impact software engineering, UI design, and modern technology courses taught by top industry pioneers.",
  "banner_url": "https://talentsea77999.b-cdn.net/assets/branding/banner_1_1724220000.jpg",
  "logo_url": "https://talentsea77999.b-cdn.net/assets/branding/logo_1_1724220000.png",
  "updated_at": "2026-08-21T12:00:00Z"
}
```

---

### 2. `PUT /api/v1/admin/branding` — Update Creator Identity Text

Updates text attributes (**Studio Name**, **Tagline**, and **Description**) when the creator modifies and saves identity details.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
Content-Type: application/json
```

#### Request Body Specification
All attributes in `BrandingUpdateRequest` support partial updating (`exclude_unset=True`). Clients may submit all text fields or only the modified fields.

##### Full Form Submission:
```json
{
  "studio_name": "Creator Academy",
  "tagline": "Learn from industry leaders",
  "description": "Your premier portal for high-impact software engineering, UI design, and modern technology courses taught by top industry pioneers."
}
```

##### Partial Update (e.g. Tagline Only):
```json
{
  "tagline": "Master Modern Engineering from Scratch"
}
```

#### Response Specification (`200 OK`)
Returns the authoritative, freshly updated creator branding object, enabling the client UI to synchronize state without issuing a secondary `GET` request.

```json
{
  "studio_name": "Creator Academy",
  "tagline": "Master Modern Engineering from Scratch",
  "description": "Your premier portal for high-impact software engineering, UI design, and modern technology courses taught by top industry pioneers.",
  "banner_url": "https://talentsea77999.b-cdn.net/assets/branding/banner_1_1724220000.jpg",
  "logo_url": "https://talentsea77999.b-cdn.net/assets/branding/logo_1_1724220000.png",
  "updated_at": "2026-08-21T12:46:00Z"
}
```

---

### 3. `POST /api/v1/admin/branding/logo` — Upload Creator Logo

Uploads a new studio/app logo image (`PNG` or `SVG`, up to 512x512px) to Bunny Storage Zone when the creator clicks **Upload Logo**.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
Content-Type: multipart/form-data
```

#### Request Body (`multipart/form-data`)
- `logo` (File, required): Image file (`PNG`, `SVG`, `JPG`, `WebP`, max 5MB).

#### Storage & CDN Path:
* Destination Path: `assets/branding/logo_{user_id}_{timestamp}.{ext}`
* Public CDN URL: `https://talentsea77999.b-cdn.net/assets/branding/logo_{user_id}_{timestamp}.{ext}`

#### Response Specification (`200 OK`)
```json
{
  "logo_url": "https://talentsea77999.b-cdn.net/assets/branding/logo_1_1724220000.png"
}
```

---

### 4. `POST /api/v1/admin/branding/banner` — Upload Creator Banner

Uploads a wide landscape cover banner image (`JPG`, `PNG`, or `WebP`) to Bunny Storage Zone when the creator uploads or replaces the **Creator Banner**.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
Content-Type: multipart/form-data
```

#### Request Body (`multipart/form-data`)
- `banner` (File, required): Image file (`JPG`, `PNG`, `WebP`, max 10MB).

#### Storage & CDN Path:
* Destination Path: `assets/branding/banner_{user_id}_{timestamp}.{ext}`
* Public CDN URL: `https://talentsea77999.b-cdn.net/assets/branding/banner_{user_id}_{timestamp}.{ext}`

#### Response Specification (`200 OK`)
```json
{
  "banner_url": "https://talentsea77999.b-cdn.net/assets/branding/banner_1_1724220000.jpg"
}
```

---

### 5. `GET /api/v1/admin/branding/theme` — Fetch Studio Theme Colors

Retrieves the active 9 white-label theme color tokens for rendering the **Theme Settings / Color Picker** UI in the Creator Studio web portal. All preset options (Netflix Dark, Cyberpunk, Midnight Blue, etc.) and color pickers are managed client-side by the website.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
```

#### Request Query Parameters — None

#### Response Specification (`200 OK`)
```json
{
  "primaryColor": "#E50914",
  "secondaryColor": "#5865F2",
  "activeStateColor": "#5865F2",
  "mainBackgroundColor": "#000000",
  "cardBackgroundColor": "#12121A",
  "primaryTextColor": "#FFFFFF",
  "secondaryTextColor": "#9CA3AF",
  "mutedTextColor": "#6B7280",
  "buttonTextColor": "#FFFFFF"
}
```

---

### 6. `PUT /api/v1/admin/branding/theme` — Update Studio Theme Colors

Updates the white-label theme color tokens when the creator saves a selected preset or custom color palette in the Studio web portal. The web portal submits **only** the 9 theme color properties.

#### Request Headers
```http
Cookie: admin_access_token=<creator_access_token>  (Primary: Browser)
Authorization: Bearer <creator_access_token>       (Fallback: Testing/Tooling)
Content-Type: application/json
```

#### Request Body Specification
All 9 color attributes must be valid hex color codes (`#RGB`, `#RRGGBB`, or `#RRGGBBAA`). Supports partial or full palette submission.

```json
{
  "primaryColor": "#E50914",
  "secondaryColor": "#5865F2",
  "activeStateColor": "#5865F2",
  "mainBackgroundColor": "#000000",
  "cardBackgroundColor": "#12121A",
  "primaryTextColor": "#FFFFFF",
  "secondaryTextColor": "#9CA3AF",
  "mutedTextColor": "#6B7280",
  "buttonTextColor": "#FFFFFF"
}
```

#### Response Specification (`200 OK`)
Returns the freshly updated authoritative 9 theme color tokens:

```json
{
  "primaryColor": "#E50914",
  "secondaryColor": "#5865F2",
  "activeStateColor": "#5865F2",
  "mainBackgroundColor": "#000000",
  "cardBackgroundColor": "#12121A",
  "primaryTextColor": "#FFFFFF",
  "secondaryTextColor": "#9CA3AF",
  "mutedTextColor": "#6B7280",
  "buttonTextColor": "#FFFFFF"
}
```

