# Creator Admin — Settings: Profile & Social Links API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints require a valid JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
The creator identity (`user_id`) is extracted directly from the authenticated session context on the backend (`Depends(get_current_user)`). No `user_id` parameter is accepted in request bodies or query strings to eliminate Insecure Direct Object Reference (IDOR) risks.

### Architecture Overview
- **Backend Service**: FastAPI (Python) handles authentication, request validation, state management, and profile updates.
- **Database**: Relational Database (Peewee ORM) stores creator profile fields (`first_name`, `last_name`, `email`, `bio`, `website`, `phone`, `location`, `avatar_url`) and social media URLs (`twitter`, `youtube`, `instagram`).
- **Cloud Storage Service**: Bunny Storage API stores and serves creator profile avatar photos (`assets/avatars/avatar_{user_id}_{timestamp}.{ext}`) via public Storage Pull Zone CDN (`https://talentsea77999.b-cdn.net`).
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
  "detail": "Could not validate credentials"
}
```

#### 3. `404 Not Found` — Creator Profile Not Found
```json
{
  "detail": "Creator profile not found"
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

Retrieves creator profile information and social links for rendering the Settings -> Profile UI page.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Request Query Parameters — None

#### Response Specification (`200 OK`)
```json
{
  "first_name": "Creator",
  "last_name": "Name",
  "email": "creator@example.com",
  "bio": "Content creator and educator",
  "website": "https://example.com",
  "phone": "+1 (555) 123-4567",
  "location": "San Francisco, CA",
  "avatar_url": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_101_1785055000.jpg",
  "social_links": {
    "twitter": "https://twitter.com/username",
    "youtube": "https://youtube.com/@username",
    "instagram": "https://instagram.com/username"
  },
  "updated_at": "2024-06-20T10:30:00Z"
}
```

---

### 2. `PUT /api/v1/admin/profile` — Update Profile & Social Settings

Updates creator profile information and social links when the creator clicks **Save Changes** (excluding `email`).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body Specification
All attributes in `ProfileUpdateRequest` are **optional**. The backend uses partial update logic (`exclude_unset=True`), meaning the client can send either a full payload or only the specific fields being updated without wiping out unmentioned database attributes.

##### Variant A: Full Form Submission (All Profile & Social Fields)
```json
{
  "first_name": "Creator",
  "last_name": "Name",
  "bio": "Content creator and educator",
  "website": "https://example.com",
  "phone": "+1 (555) 123-4567",
  "location": "San Francisco, CA",
  "social_links": {
    "twitter": "https://twitter.com/username",
    "youtube": "https://youtube.com/@username",
    "instagram": "https://instagram.com/username"
  }
}
```

##### Variant B: Partial Field Update (Single or Few Fields)
```json
{
  "bio": "Updated channel bio description only"
}
```

##### Variant C: Social Links Only Update
```json
{
  "social_links": {
    "twitter": "https://twitter.com/newhandle",
    "youtube": "https://youtube.com/@newchannel",
    "instagram": "https://instagram.com/newprofile"
  }
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 3. `POST /api/v1/admin/profile/photo` — Upload Avatar Image (Change Avatar)

Uploads a new avatar image (`JPG` or `PNG`, max 2MB) to Bunny Storage Zone when the creator clicks **Change Avatar**.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: multipart/form-data
```

#### Request Body (`multipart/form-data`)
- `photo` (File, required): Image file (JPG or PNG, max 2MB).

#### Response Specification (`200 OK`)
```json
{
  "avatar_url": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_101_1785055000.jpg"
}
```
