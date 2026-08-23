---
name: fastapi-peewee-clean-architecture
description: Layered architecture rules for FastAPI + Peewee ORM projects. Enforces Separation of Concerns between Routes, Services, Repositories, Schemas (DTOs), and Models, IDOR security (no user_id in payloads), IST timezone handling, and database connection lifecycle management.
---

# FastAPI + Peewee ORM Clean Architecture Skill

## Overview
This skill documents architectural guidelines, security controls, and design patterns for building modular, maintainable FastAPI applications powered by **Peewee ORM**.

---

## 1. Strict 5-Layer Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Routes Layer (app/routes/): HTTP Handlers, Auth & Query Validation       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Services Layer (app/services/): Business Logic & Cloud Orchestration     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Repositories Layer (app/repositories/): Peewee DB CRUD Queries           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Schemas Layer (app/schemas/): Pydantic DTO Validation & JSON Envelopes   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Models Layer (app/models/): Peewee ORM Entities (BaseModel -> db_proxy) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibility Rules
1. **Route Handlers (`app/routes/`)**:
   - MUST NOT execute direct SQL or Peewee ORM queries.
   - Validates requests using Pydantic Schemas and injects authentication dependencies (`CurrentAdmin` / `CurrentSubscriber`).
   - Delegates all business logic to Service classes.
2. **Services Layer (`app/services/`)**:
   - Executes business rules, cloud API calls (Bunny Stream / Storage), and signature calculations.
   - Calls Repositories for data access.
3. **Repositories Layer (`app/repositories/`)**:
   - Encapsulates all Peewee ORM queries (`Model.select()`, `Model.create()`, `model.save()`).
   - Handles pagination logic using `.paginate(page, limit)`.
4. **Schemas Layer (`app/schemas/`)**:
   - Pure Pydantic v2 request and response contracts.
   - Use `model_dump(exclude_unset=True)` for safe partial updates.
5. **Models Layer (`app/models/`)**:
   - Peewee entities inheriting from `BaseModel` bound to global `db_proxy`.

---

## 2. Security Standards & IDOR Prevention

### Insecure Direct Object Reference (IDOR) Rules
- `user_id` MUST NEVER be accepted in request bodies or query parameters for protected resources.
- `user_id` is extracted strictly from the validated JWT Bearer token context (`CurrentAdmin` / `CurrentSubscriber`).
- Every read, update, or delete operation MUST filter by both `resource_id` AND `user_id`:
  ```python
  video = Video.get_or_none((Video.id == video_id) & (Video.user == user_id))
  ```

---

## 3. Indian Standard Time (IST) Guidelines
- Video scheduling and user-facing release timers use **Indian Standard Time (`Asia/Kolkata`, UTC+05:30)**:
  ```python
  from zoneinfo import ZoneInfo
  scheduled_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Kolkata"))
  ```
- Internal audit timestamps (`created_at`, `updated_at`) are saved in UTC.

---

## 4. Peewee Database Connection Lifecycle
- Database connections are opened and closed per HTTP request via `PeeweeDBMiddleware` in `app/middleware/db_middleware.py`.
- Always verify `db_proxy.is_closed()` before calling `db_proxy.connect()` or `db_proxy.close()`.
