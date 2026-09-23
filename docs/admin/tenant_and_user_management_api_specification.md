# Platform Multi-Tenant & Admin User Management API Specification

This specification defines the complete platform architecture, Super Admin controls, tenant provisioning workflows, and multi-tenant administrator lifecycle endpoints for the **TalentSea Platform** (`/api/v1/admin/tenants/*` and `/api/v1/admin/users/*`).

---

## 1. System Architecture & Multi-Tenant Model

### 1.1 Architectural Hierarchy

The platform operates on a **Shared-Database, Tenant-Discriminator Multi-Tenant Architecture**:

```
                       ┌───────────────────────────────┐
                       │     PLATFORM SUPER ADMIN      │
                       │   (tenant_id=NULL, role=sa)   │
                       └───────────────┬───────────────┘
                                       │
                      Cross-Tenant Management & Switching
                             (via X-Tenant-Id header)
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│     TENANT 1 (e.g. Studio A)  │             │     TENANT 2 (e.g. Studio B)  │
│  - Name, Slug, Logo, Banner   │             │  - Name, Slug, Logo, Banner   │
│  - is_active: True/False      │             │  - is_active: True/False      │
└───────────────┬───────────────┘             └───────────────┬───────────────┘
                │                                             │
      Tenant Admins & Owners                        Tenant Admins & Owners
  (tenant_id=1, role="admin")                   (tenant_id=2, role="admin")
                │                                             │
      Tenant-Scoped Resources                       Tenant-Scoped Resources
  - Videos (tenant_id=1)                        - Videos (tenant_id=2)
  - Playlists (tenant_id=1)                     - Playlists (tenant_id=2)
  - Categories (tenant_id=1)                    - Categories (tenant_id=2)
  - Subscription Plans (tenant_id=1)            - Subscription Plans (tenant_id=2)
  - Subscribers & Telemetry                     - Subscribers & Telemetry
```

### 1.2 Roles & Permission Matrix

| Role                | `tenant_id` | `is_owner` | Scope / Capabilities                                                                                                                                                                                                                                      |
| :------------------ | :---------: | :--------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`super_admin`**   |   `NULL`    |  `False`   | **Platform Master Authority**: Can provision new tenants, list/view all tenants across the platform, toggle tenant active status, and switch operational tenant context via `X-Tenant-Id` header (falling back to first tenant).                          |
| **`admin` (Owner)** |    `> 0`    |   `True`   | **Tenant Creator / Studio Owner**: Provisioned when the tenant is registered. Has full control over the studio's videos, playlists, categories, plans, comments, branding, and additional staff admins. Cannot be deleted or deactivated by staff admins. |
| **`admin` (Staff)** |    `> 0`    |  `False`   | **Tenant Studio Staff**: Additional administrators invited to manage content within the specific tenant studio.                                                                                                                                           |

### 1.3 Tenant Context Switching for Super Admins

Super Admins can execute standard admin endpoints (e.g., uploading videos, viewing playlists, configuring branding) on behalf of any tenant using the **`X-Tenant-Id`** HTTP header:

```http
GET /api/v1/admin/videos HTTP/1.1
Host: api.talentsea.com
Authorization: Bearer <super_admin_access_token>
X-Tenant-Id: 2
```

- If `X-Tenant-Id` is provided, the backend resolves and validates tenant `2`.
- If `X-Tenant-Id` is omitted, the backend **automatically defaults to the first active tenant** (`Tenant.select().order_by(Tenant.id.asc()).first()`), ensuring a seamless dashboard experience.
- Regular tenant admins are strictly pinned to their own `admin.tenant_id`; any `X-Tenant-Id` header supplied by a regular admin is ignored.

---

## 2. Super Admin — Tenant Management Endpoints

All endpoints in this section require **Super Admin privileges** (`role == "super_admin"`). Requests from regular admins return `403 Forbidden`.

### 2.1 `POST /api/v1/admin/tenants` — Provision New Tenant

Atomically creates a new Tenant studio, provisions its initial owner Admin account, and seeds the standard default subscription plans (`with_ads` and `no_ads`).

#### Request Headers

```http
Authorization: Bearer <super_admin_jwt>
Content-Type: application/json
```

#### Request Body

```json
{
  "name": "Acme Media Studio",
  "tagline": "Premium Film & Documentaries",
  "description": "The home of award-winning independent films and documentaries.",
  "admin_email": "owner@acmestudio.com",
  "admin_password": "SecurePassword123!",
  "admin_first_name": "Jane",
  "admin_last_name": "Doe",
  "admin_phone": "+15551234567"
}
```

| Field              | Type     | Required | Description                                                              |
| :----------------- | :------- | :------: | :----------------------------------------------------------------------- |
| `name`             | `string` | **Yes**  | Studio / brand name (2-255 chars). Backend auto-derives URL-safe `slug`. |
| `tagline`          | `string` |    No    | Public studio tagline (max 255 chars).                                   |
| `description`      | `string` |    No    | Studio description text.                                                 |
| `admin_email`      | `string` | **Yes**  | Valid email for the initial tenant owner admin.                          |
| `admin_password`   | `string` | **Yes**  | Password for the owner account (min 8 chars).                            |
| `admin_first_name` | `string` | **Yes**  | First name of owner.                                                     |
| `admin_last_name`  | `string` | **Yes**  | Last name of owner.                                                      |
| `admin_phone`      | `string` |    No    | Owner phone number (max 50 chars).                                       |

#### Response (`201 Created`)

```json
{
  "id": 2,
  "owner_id": 14,
  "name": "Acme Media Studio",
  "slug": "acme-media",
  "tagline": "Premium Film & Documentaries",
  "description": "The home of award-winning independent films and documentaries.",
  "is_active": true,
  "created_at": "2026-09-22T10:00:00Z"
}
```

#### Response Fields

| Field         | Type      | Description                                                                                             |
| :------------ | :-------- | :------------------------------------------------------------------------------------------------------ |
| `id`          | `integer` | Database ID of the newly created Tenant studio.                                                         |
| `owner_id`    | `integer` | Database ID of the newly provisioned Admin account that acts as the initial owner of this Tenant.       |
| `name`        | `string`  | Studio brand name.                                                                                      |
| `slug`        | `string`  | URL-safe slug auto-derived from the name.                                                               |
| `tagline`     | `string`  | Public studio tagline.                                                                                  |
| `description` | `string`  | Studio description text.                                                                                |
| `is_active`   | `boolean` | Always `true` on creation. Indicates the studio is live.                                                |
| `created_at`  | `string`  | ISO-8601 timestamp of creation.                                                                         |

---

### 2.2 `GET /api/v1/admin/tenants` — List All Tenants

Returns a list of registered tenants on the platform for studio selection, switching, and status governance. Supports both a compact array for quick selection and a detailed paginated view with operational metrics.

#### Request Headers

```http
Authorization: Bearer <super_admin_jwt>
```

#### Query Parameters

| Parameter   | Type      | Default   | Description                                                                   |
| :---------- | :-------- | :-------: | :---------------------------------------------------------------------------- |
| `mode`      | `string`  | `compact` | Response format mode. Options: `compact` (flat list) or `detailed` (paginated)|
| `page`      | `integer` | `1`       | Page number for pagination (only applies to `mode=detailed`).                 |
| `limit`     | `integer` | `20`      | Items per page (only applies to `mode=detailed`, max `100`).                  |
| `is_active` | `boolean` | `null`    | Optional filter by active status (`true` / `false`).                          |
| `search`    | `string`  | `null`    | Optional substring filter on tenant `name`.                                   |

#### Response 1 (`200 OK`) — `mode=compact` (Default)

```json
[
  {
    "id": 1,
    "name": "Content Talent",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Acme Media Studio",
    "is_active": false
  }
]
```

#### Response 2 (`200 OK`) — `mode=detailed`

```json
{
  "total": 12,
  "page": 1,
  "limit": 10,
  "total_pages": 2,
  "items": [
    {
      "id": 1,
      "name": "Content Talent",
      "slug": "content-talent",
      "tagline": "Official Talent Studio",
      "description": "Main platform studio channel.",
      "is_active": true,
      "logo_url": "https://talentsea.b-cdn.net/assets/logo.png",
      "deactivation_reason": null,
      "deactivated_at": null,
      "created_at": "2026-09-01T08:00:00Z",
      "updated_at": "2026-09-22T11:00:00Z",
      "admins_count": 2,
      "videos_count": 48,
      "subscribers_count": 1420
    }
  ]
}
```

---

### 2.3 `GET /api/v1/admin/tenants/{tenant_id}` — Get Single Tenant Details

Retrieves full profile and telemetry metadata for a specific tenant.

#### Request Headers

```http
Authorization: Bearer <super_admin_jwt>
```

#### Response (`200 OK`)

```json
{
  "id": 1,
  "name": "Content Talent",
  "slug": "content-talent",
  "tagline": "Official Talent Studio",
  "description": "Main platform studio channel.",
  "logo_url": "https://talentsea77999.b-cdn.net/assets/branding/logo_1_1724220000.png",
  "deactivation_reason": null,
  "deactivated_at": null,
  "created_at": "2026-09-01T08:00:00Z",
  "updated_at": "2026-09-15T12:00:00Z",
  "admins_count": 2,
  "videos_count": 48,
  "subscribers_count": 1420
}
```

---

### 2.4 `PATCH /api/v1/admin/tenants/{tenant_id}/status` — Toggle Tenant Status

Activates or deactivates an entire tenant studio. When deactivated:

- All tenant administrators are blocked from logging in.
- Mobile subscribers attempting to load content under this tenant receive `403 Forbidden` / `"Tenant studio is currently suspended"`.
- Ad monetization and background settlement disbursements are paused.

#### Request Body

```json
{
  "is_active": false,
  "deactivation_reason": "Violation of terms of service"
}
```

#### Response (`200 OK`)

```json
{
  "id": 1,
  "name": "Content Talent",
  "slug": "content-talent",
  "tagline": "Official Talent Studio",
  "description": "Main platform studio channel.",
  "is_active": false,
  "logo_url": null,
  "deactivation_reason": "Violation of terms of service",
  "deactivated_at": "2026-09-22T11:00:00Z",
  "created_at": "2026-09-01T08:00:00Z",
  "updated_at": "2026-09-22T11:00:00Z",
  "admins_count": 2,
  "videos_count": 48,
  "subscribers_count": 1420
}
```

---

## 3. Tenant Admin & Staff Management Endpoints

Endpoints in this section (`/api/v1/admin/users/*`) allow tenant owners (or super admins acting within the tenant context) to manage dashboard administrator accounts bound to the active tenant.

### 3.1 `GET /api/v1/admin/users` — List Tenant Administrators

Returns all administrator accounts belonging to the active tenant.

#### Request Headers

```http
Authorization: Bearer <admin_jwt>
```

#### Response (`200 OK`)

```json
[
  {
    "id": 2,
    "email": "owner@studio.com",
    "first_name": "Madhu",
    "last_name": "Jakka",
    "phone": null,
    "role": "admin",
    "is_owner": true,
    "is_active": true,
    "avatar_url": null,
    "created_at": "2026-09-01T08:00:00Z"
  },
  {
    "id": 3,
    "email": "editor@studio.com",
    "first_name": "Alex",
    "last_name": "Smith",
    "phone": "+15559990000",
    "role": "admin",
    "is_owner": false,
    "is_active": true,
    "avatar_url": "https://cdn.example.com/avatars/3.png",
    "created_at": "2026-09-10T14:30:00Z"
  }
]
```

---

### 3.2 `POST /api/v1/admin/users` — Invite / Create Staff Admin

Adds an additional administrator user to the current tenant studio.

#### Request Body

```json
{
  "email": "editor@studio.com",
  "password": "TemporaryPassword123!",
  "first_name": "Alex",
  "last_name": "Smith",
  "role": "admin"
}
```

#### Response (`201 Created`)

```json
{
  "id": 3,
  "email": "editor@studio.com",
  "first_name": "Alex",
  "last_name": "Smith",
  "role": "admin",
  "is_owner": false,
  "is_active": true,
  "avatar_url": null,
  "created_at": "2026-09-22T11:30:00Z"
}
```

---

### 3.3 `PATCH /api/v1/admin/users/{admin_id}/status` — Toggle Admin User Status

Enables or disables an administrator account within the tenant.

- A tenant owner **cannot deactivate their own account** (`400 Bad Request: "Cannot change status of the tenant owner"`).

#### Request Body

```json
{
  "is_active": false
}
```

#### Response (`200 OK`)

Returns the updated `AdminUserResponse`.

---

### 3.4 `DELETE /api/v1/admin/users/{admin_id}` — Remove Admin User

Permanently removes a staff administrator account from the tenant.

- **Safety Rule**: Tenant owners (`is_owner == True`) cannot be deleted (`400 Bad Request: "Cannot delete the tenant owner account"`).

#### Response (`204 No Content`)

No content returned on success.
