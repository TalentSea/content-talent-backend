# Mobile Subscriber — Comments API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
- **Public Feed Reading (`GET`)**: Optional Subscriber authentication via `get_optional_subscriber`. Guest users can view comments, but `is_liked` returns `false` and `is_owner` returns `false`.
- **Protected Actions (`POST`, `DELETE`)**: Requires a valid Subscriber JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <subscriber_access_token>
```

### Author DTO Object Standard
All comment endpoints encapsulate author metadata inside a unified `author` object with real-time profile consistency:
- `id` (integer): ID of the comment author.
- `name` (string): Live display name of the author.
- `avatar_url` (string or null): Live avatar image URL.
- `is_creator` (boolean): `true` if posted by the content creator (Admin), `false` if posted by a subscriber.
- `is_hearted_by_creator` (boolean): `true` if the Admin Creator gave this comment a **"❤️ Creator Heart"** badge, `false` otherwise.

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
      "is_hearted_by_creator": true,
      "is_liked": true,
      "reply_count": 14,
      "is_owner": false,
      "created_at": "2026-08-18T14:22:00Z"
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
  "is_hearted_by_creator": false,
  "is_liked": false,
  "reply_count": 0,
  "is_owner": true,
  "created_at": "2026-08-22T01:00:00Z"
}
```

---

### 3. `GET /api/v1/mobile/comments/{comment_id}/replies` — Get Thread Replies (Paginated)

Retrieves a paginated list of nested reply comments for a specific parent comment.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>  # Optional
```

#### Path Parameters
- `comment_id` (integer, required): ID of the parent comment.

#### Request Query Parameters

| Param | Type | Required | Description |
|---|---|---|---|
| `page` | `integer` | No | Page number (default `1`) |
| `limit` | `integer` | No | Items per page (default `10`, max `50`) |

#### Response Specification (`200 OK`)
```json
{
  "total": 14,
  "page": 1,
  "limit": 10,
  "total_pages": 2,
  "items": [
    {
      "id": 9202,
      "text": "Thank you Sarah! Glad you liked it.",
      "author": {
        "id": 1,
        "name": "TechNics Training",
        "avatar_url": "https://talentsea77999.b-cdn.net/avatars/creator_1.jpg",
        "is_creator": true
      },
      "likes": 12,
      "is_hearted_by_creator": false,
      "is_liked": false,
      "is_owner": false,
      "created_at": "2026-08-22T01:05:00Z"
    }
  ]
}
```

---

### 4. `POST /api/v1/mobile/comments/{comment_id}/replies` — Post Thread Reply

Posts a reply nested under a parent comment.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
Content-Type: application/json
```

#### Path Parameters
- `comment_id` (integer, required): ID of the parent comment.

#### Request Body
```json
{
  "text": "I had the same question too!"
}
```

#### Response Specification (`201 Created`)
```json
{
  "id": 9203,
  "text": "I had the same question too!",
  "author": {
    "id": 4512,
    "name": "Sarah Connor",
    "avatar_url": "https://talentsea77999.b-cdn.net/avatars/user_4512.jpg",
    "is_creator": false
  },
  "likes": 0,
  "is_hearted_by_creator": false,
  "is_liked": false,
  "is_owner": true,
  "created_at": "2026-08-22T01:10:00Z"
}
```

---

### 5. `POST /api/v1/mobile/comments/{comment_id}/like` — Toggle Comment Like

Toggles like on a comment for the authenticated subscriber.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Path Parameters
- `comment_id` (integer, required): ID of the comment to like/unlike.

#### Response Specification (`200 OK`)
```json
{
  "comment_id": 9201,
  "likes_count": 43,
  "is_liked": true
}
```

---

### 6. `DELETE /api/v1/mobile/comments/{comment_id}` — Delete Own Comment

Deletes a comment posted by the authenticated subscriber.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Path Parameters
- `comment_id` (integer, required): ID of the comment to delete.

#### Response Specification (`200 OK`)
```json
{
  "success": true,
  "message": "Comment deleted successfully"
}
```
