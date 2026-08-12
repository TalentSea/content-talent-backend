# Mobile Subscriber — Comments API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
- **Public Feed Reading (`GET`)**: Optional Subscriber authentication via `get_optional_subscriber`. Guest users can view comments, but `is_liked` returns `false` and `is_owner` returns `false`.
- **Protected Actions (`POST`, `DELETE`)**: Requires a valid Subscriber JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <subscriber_access_token>
```

### Author DTO Object Standard
All comment endpoints encapsulate author metadata inside a unified `author` object:
- `id` (integer): ID of the comment author.
- `name` (string): Display name of the author.
- `avatar_url` (string or null): Avatar image URL.
- `is_creator` (boolean): `true` if posted by the content creator (Admin), `false` if posted by a subscriber.

---

## 💬 Mobile Comments Endpoints

### 1. `GET /api/v1/mobile/videos/{video_id}/comments` — List Video Comments (Paginated)

Retrieves a paginated list of top-level comments for a specific video.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>  # Optional
```

#### Path Parameters
- `video_id` (integer, required): ID of the target video.

#### Request Query Parameters

| Param | Type | Required | Description |
|---|---|---|---|
| `sort` | `string` | No | Sort order: `newest` (default), `oldest`, `most_liked` |
| `page` | `integer` | No | Page number (default `1`) |
| `limit` | `integer` | No | Items per page (default `20`, max `100`) |

#### Response Specification (`200 OK`)
```json
{
  "total": 142,
  "page": 1,
  "limit": 20,
  "total_pages": 8,
  "items": [
    {
      "id": 8912,
      "text": "Great explanation on FastAPI dependency injection!",
      "author": {
        "id": 4512,
        "name": "Sarah Connor",
        "avatar_url": "https://talentsea77999.b-cdn.net/avatars/user_4512.jpg",
        "is_creator": false
      },
      "likes": 42,
      "is_liked": true,
      "reply_count": 14,
      "is_owner": false,
      "created_at": "2024-06-18T14:22:00Z"
    }
  ]
}
```

---

### 2. `POST /api/v1/mobile/videos/{video_id}/comments` — Post New Top-Level Comment

Posts a new top-level comment under a video.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): ID of the target video.

#### Request Body
```json
{
  "text": "Amazing episode! Thanks for sharing."
}
```

#### Response Specification (`201 Created`)
```json
{
  "id": 9201,
  "text": "Amazing episode! Thanks for sharing.",
  "author": {
    "id": 4512,
    "name": "Sarah Connor",
    "avatar_url": "https://talentsea77999.b-cdn.net/avatars/user_4512.jpg",
    "is_creator": false
  },
  "likes": 0,
  "is_liked": false,
  "reply_count": 0,
  "is_owner": true,
  "created_at": "2024-08-12T10:00:00Z"
}
```

---

### 3. `GET /api/v1/mobile/comments/{id}/replies` — Fetch Thread Replies (Paginated)

Retrieves a paginated list of child replies nested under a specific top-level comment.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>  # Optional
```

#### Path Parameters
- `id` (integer, required): ID of the top-level parent comment.

#### Request Query Parameters

| Param | Type | Required | Description |
|---|---|---|---|
| `sort` | `string` | No | Sort order: `oldest` (default, thread chronological order) or `newest` |
| `page` | `integer` | No | Page number (default `1`) |
| `limit` | `integer` | No | Items per page (default `20`, max `100`) |

#### Response Specification (`200 OK`)
```json
{
  "total": 14,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 9001,
      "comment_id": 8912,
      "text": "Thank you Sarah! Glad you found it useful.",
      "author": {
        "id": 101,
        "name": "Alex Tech",
        "avatar_url": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_101_1785055000.jpg",
        "is_creator": true
      },
      "likes": 12,
      "is_liked": true,
      "is_owner": false,
      "created_at": "2024-06-18T15:00:00Z"
    }
  ]
}
```

---

### 4. `POST /api/v1/mobile/comments/{id}/replies` — Post Reply to Comment / Sub-Comment

Posts a reply to a comment or sub-comment. Automatically links to the root top-level parent comment thread.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
Content-Type: application/json
```

#### Path Parameters
- `id` (integer, required): ID of the parent comment or sub-comment being replied to.

#### Request Body
```json
{
  "text": "@Alex when is Part 4 coming out?"
}
```

#### Response Specification (`201 Created`)
```json
{
  "id": 9302,
  "comment_id": 8912,
  "text": "@Alex when is Part 4 coming out?",
  "author": {
    "id": 4512,
    "name": "Sarah Connor",
    "avatar_url": "https://talentsea77999.b-cdn.net/avatars/user_4512.jpg",
    "is_creator": false
  },
  "likes": 0,
  "is_liked": false,
  "is_owner": true,
  "created_at": "2024-08-12T10:15:00Z"
}
```

---

### 5. `POST /api/v1/mobile/comments/{id}/like` — Toggle Comment Like

Toggles authenticated subscriber's like state on a comment or reply.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Path Parameters
- `id` (integer, required): ID of the comment to like/unlike.

#### Request Body — None

#### Response Specification (`200 OK`)
```json
{
  "status": "success",
  "is_liked": true,
  "likes": 43
}
```

---

### 6. `DELETE /api/v1/mobile/comments/{id}` — Delete Own Comment

Deletes a comment permanently. Allowed only if the comment belongs to the authenticated subscriber (`comment.user == subscriber_id`).

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Path Parameters
- `id` (integer, required): ID of the comment to remove.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```
