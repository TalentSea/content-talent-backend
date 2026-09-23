# Notification System — Architecture Review & Technical Specification

## 1. Executive Summary & Objectives

The **Notification System** provides an enterprise-grade, multi-tenant notification delivery pipeline for the White-Labeled Creator OTT Platform. It drives user engagement, retention, and subscription revenue across two delivery channels:

1. **In-App Notification Feed (Bell Icon Inbox)**:
   - Database-persisted activity log stored per subscriber.
   - Powers the in-app notification center with read/unread statuses (`is_read`), timestamps, deep-link navigation metadata, and badge counters.
2. **Push Notifications (Firebase Cloud Messaging - FCM & APNs)**:
   - Device-targeted alerts waking up mobile applications on lock-screens and notification trays when the app is backgrounded or terminated.

---

## 2. Event Catalog & Trigger Matrix

| Event Category | Trigger Condition | Target Deep-Link | Delivery Channels |
| :--- | :--- | :--- | :--- |
| **`video_published`** | Creator publishes a new video or scheduled publisher worker releases content | `{"target_type": "video", "target_id": 104}` | In-App Feed + Push |
| **`comment_heart`** | Creator hearts a subscriber's comment | `{"target_type": "comment", "target_id": 45}` | In-App Feed + Push |
| **`comment_reply`** | Creator or subscriber replies to a comment thread | `{"target_type": "comment", "target_id": 46}` | In-App Feed + Push |
| **`subscription_active`**| Razorpay payment captured & user subscription created | `{"target_type": "subscription", "target_id": 12}` | In-App Feed + Push |
| **`subscription_expiring`**| Automated background cron detects subscription expires in 3 days | `{"target_type": "plans", "target_id": null}` | In-App Feed + Push |
| **`subscription_expired`** | Subscription expiration worker changes state to expired | `{"target_type": "plans", "target_id": null}` | In-App Feed + Push |
| **`creator_broadcast`** | Admin Creator sends a custom announcement blast | Custom deep link or announcement modal | In-App Feed + Push |

---

## 3. Database Architecture & Schema Specification

The notification engine introduces **two new database tables** (bringing the platform to 25 total tables).

### Table 1: `notifications` (In-App Notification Ledger)

* **Model File**: `app/models/notification.py`
* **Table Name**: `notifications`

```python
class Notification(BaseModel):
    tenant = ForeignKeyField(Tenant, column_name="tenant_id", backref="notifications", on_delete="CASCADE")
    subscriber = ForeignKeyField(Subscriber, column_name="subscriber_id", backref="notifications", on_delete="CASCADE")
    title = CharField(max_length=255)
    message = TextField()
    type = CharField(max_length=50)  # e.g., 'video_published', 'comment_heart', 'creator_broadcast'
    target_type = CharField(max_length=50, null=True)  # 'video', 'playlist', 'comment', 'subscription', 'plans'
    target_id = IntegerField(null=True)  # Resource primary key ID
    image_url = CharField(max_length=500, null=True)
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "notifications"
        indexes = (
            (("subscriber", "is_read"), False),
            (("subscriber", "created_at"), False),
        )
```

| Field Name | Type | Key / Constraint | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | **PK (Auto Increment)** | NO | Auto | Primary key ID |
| `tenant_id` | `INTEGER` | **FK ➔ `tenants.id` (CASCADE)** | NO | None | Creator Studio tenant boundary |
| `subscriber_id` | `INTEGER` | **FK ➔ `subscribers.id` (CASCADE)** | NO | None | Recipient subscriber or guest |
| `title` | `VARCHAR(255)` | Standard | NO | None | Short notification headline |
| `message` | `TEXT` | Standard | NO | None | Message body text |
| `type` | `VARCHAR(50)` | Standard | NO | None | Event category code |
| `target_type` | `VARCHAR(50)` | Standard | YES | `NULL` | Navigation deep link resource |
| `target_id` | `INTEGER` | Standard | YES | `NULL` | Target resource primary key ID |
| `image_url` | `VARCHAR(500)` | Standard | YES | `NULL` | Optional thumbnail / icon image URL |
| `is_read` | `BOOLEAN` | Standard (Indexed) | NO | `False` | Read status indicator |
| `read_at` | `DATETIME` | Standard | YES | `NULL` | Timestamp when user opened notification |
| `created_at` | `DATETIME` | Standard (Indexed) | NO | `UTC timestamp` | Creation timestamp |

---

### Table 2: `device_tokens` (Push Device Hardware Registry)

* **Model File**: `app/models/notification.py`
* **Table Name**: `device_tokens`

```python
class DeviceToken(BaseModel):
    subscriber = ForeignKeyField(Subscriber, column_name="subscriber_id", backref="device_tokens", on_delete="CASCADE")
    token = CharField(max_length=500, unique=True, index=True)
    platform = CharField(max_length=20)  # 'ios', 'android', 'web'
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "device_tokens"
```

| Field Name | Type | Key / Constraint | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | **PK (Auto Increment)** | NO | Auto | Primary key ID |
| `subscriber_id` | `INTEGER` | **FK ➔ `subscribers.id` (CASCADE)** | NO | None | Owner subscriber session |
| `token` | `VARCHAR(500)` | **UNIQUE, INDEX** | NO | None | Unique FCM/APNs device registration token |
| `platform` | `VARCHAR(20)` | Standard | NO | None | Operating system (`"ios"`, `"android"`) |
| `is_active` | `BOOLEAN` | Standard | NO | `True` | Token validity state |
| `created_at` | `DATETIME` | Standard | NO | `UTC timestamp` | Initial registration timestamp |
| `updated_at` | `DATETIME` | Standard | NO | `UTC timestamp` | Last update / refresh timestamp |

---

## 4. Mobile Subscriber API Specifications

All mobile notification endpoints require standard `Authorization: Bearer <access_token>` authentication.

### 1. `GET /api/v1/mobile/notifications` — List In-App Notifications Feed
* **Method**: `GET`
* **Query Parameters**:
  - `page` (int, default: 1)
  - `limit` (int, default: 20, max: 100)
* **Response Payload (`200 OK`)**:
  ```json
  {
    "unread_count": 3,
    "total": 15,
    "page": 1,
    "limit": 20,
    "total_pages": 1,
    "items": [
      {
        "id": 89,
        "title": "New Video Released",
        "message": "Full-Stack Web Development Episode 14 is now live!",
        "type": "video_published",
        "target_type": "video",
        "target_id": 104,
        "image_url": "https://pull-zone.b-cdn.net/assets/thumb_104.jpg",
        "is_read": false,
        "created_at": "2026-09-19T10:00:00Z"
      },
      {
        "id": 82,
        "title": "Creator Liked Your Comment",
        "message": "TechCreator loved: 'Great explanation on Peewee ORM!'",
        "type": "comment_heart",
        "target_type": "comment",
        "target_id": 45,
        "image_url": null,
        "is_read": true,
        "created_at": "2026-09-18T16:20:00Z"
      }
    ]
  }
  ```

---

### 2. `GET /api/v1/mobile/notifications/unread-count` — Fast Badge Counter
* **Method**: `GET`
* **Execution Time**: `< 1ms` (executes `COUNT(id) WHERE subscriber_id = :id AND is_read = false` leveraging composite index).
* **Response Payload (`200 OK`)**:
  ```json
  {
    "unread_count": 3
  }
  ```

---

### 3. `PATCH /api/v1/mobile/notifications/{id}/read` — Mark Single Notification as Read
* **Method**: `PATCH`
* **Path Parameter**: `id` (integer)
* **Response Payload (`200 OK`)**:
  ```json
  {
    "id": 89,
    "is_read": true,
    "read_at": "2026-09-19T13:45:00Z"
  }
  ```

---

### 4. `POST /api/v1/mobile/notifications/read-all` — Mark All as Read
* **Method**: `POST`
* **Response Payload (`200 OK`)**:
  ```json
  {
    "success": true,
    "marked_count": 3
  }
  ```

---

### 5. `DELETE /api/v1/mobile/notifications/{id}` — Delete Notification
* **Method**: `DELETE`
* **Response Payload (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Notification deleted successfully"
  }
  ```

---

### 6. `POST /api/v1/mobile/notifications/device-token` — Register / Refresh Push Token
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "token": "fcm_reg_token_abc123456...",
    "platform": "android"
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Device token registered successfully"
  }
  ```

---

## 5. Creator Admin Studio API Specifications

### 1. `POST /api/v1/admin/notifications/broadcast` — Send Creator Studio Announcement
* **Method**: `POST`
* **Auth**: `CurrentAdmin` (JWT Cookie or Bearer header)
* **Request Body**:
  ```json
  {
    "title": "Live Q&A Session Tomorrow",
    "message": "Join us this Friday at 7 PM for exclusive subscriber Q&A!",
    "target_type": "none",
    "target_id": null,
    "send_push": true
  }
  ```
* **Response Payload (`201 Created`)**:
  ```json
  {
    "success": true,
    "recipient_count": 1420,
    "message": "Broadcast scheduled and dispatched"
  }
  ```

---

## 6. High-Performance Dispatcher & Architecture

```
                                      TRIGGER EVENT
                (Video Published / Comment Heart / Billing / Creator Broadcast)
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │    Notification Dispatcher    │
                             └───────────────┬───────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
        [In-App Database Insert]                           [Push Notification Service]
      • Peewee `insert_many` in batches                  • Background `asyncio` task
      • Tenant-isolated (`tenant_id`)                   • Firebase Cloud Messaging (FCM)
      • Sub-50ms bulk execution                          • Auto-deactivates uninstalled tokens
```

1. **High-Performance Fan-Out**:
   * Broadcasting an announcement to 5,000 subscribers using individual `.create()` calls would cause 5,000 SQL queries and stall HTTP workers.
   * We utilize Peewee batch chunking:
     ```python
     with db_proxy.atomic():
         for chunk in chunked_records:
             Notification.insert_many(chunk).execute()
     ```
   * 5,000 notifications commit in `< 50ms`.

2. **Asynchronous Non-Blocking Push Execution**:
   * FCM API network requests run within background `asyncio.create_task` worker routines. The client initiating the action receives immediate sub-20ms HTTP responses without waiting for Google FCM servers.

3. **Stale Token Pruning**:
   * If FCM returns `UNREGISTERED` or `410 Gone` (user uninstalled the app), the worker updates `DeviceToken.is_active = False` to prevent unnecessary outbound traffic.

---

## 7. Implementation Roadmap

1. **Model Layer**: Create `app/models/notification.py`, export in `app/models/__init__.py`, register in `app/database.py`.
2. **Schemas**: Create `app/schemas/mobile/notification_schemas.py` and `app/schemas/admin/notification_schemas.py`.
3. **Data Access**: Implement `app/repositories/mobile/notification_repository.py` and `app/repositories/admin/notification_repository.py`.
4. **Services**: Implement `app/services/mobile/notification_service.py` and dispatcher utility.
5. **Routes**: Register `app/routes/mobile/notification_routes.py` and `app/routes/admin/notification_routes.py` in `app/main.py`.
6. **Documentation**: Create `docs/mobile/notifications_api_specification.md` and `docs/admin/notifications_api_specification.md`.
