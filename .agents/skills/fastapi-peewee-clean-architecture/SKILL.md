---
name: fastapi-peewee-clean-architecture
description: Layered architecture rules for FastAPI + Peewee ORM projects. Enforces Separation of Concerns between Routes, Services, Repositories, Schemas (DTOs), and Models, IDOR security (no user_id in payloads), IST timezone handling, environment configuration decoupling, and database connection lifecycle management.
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
   - Translates domain exceptions into standard HTTP error responses.
2. **Services Layer (`app/services/`)**:
   - Executes business rules, cloud API calls (Bunny Stream / Storage, Razorpay), and signature calculations.
   - Calls Repositories for data access.
   - Remains framework-agnostic where possible.
3. **Repositories Layer (`app/repositories/`)**:
   - Encapsulates all Peewee ORM queries (`Model.select()`, `Model.create()`, `model.save()`).
   - Enforces multi-tenant isolation by filtering on `creator_id` or `user_id`.
   - Handles pagination logic using `.paginate(page, limit)`.
4. **Schemas Layer (`app/schemas/`)**:
   - Pure Pydantic v2 request and response contracts.
   - Use `model_dump(exclude_unset=True)` for safe partial updates.
5. **Models Layer (`app/models/`)**:
   - Peewee entities inheriting from `BaseModel` bound to global `db_proxy`.
   - Explicit indexes on foreign keys and frequently filtered columns.

---

## 2. Environment Settings & Decision-Making Values Standard

All business thresholds, timeouts, intervals, and weights MUST be declared in `app/config.py` using Pydantic `BaseSettings`:
* **Never Hardcode Numbers**: Any threshold (percentages, cooldown minutes, caps, weights) must be read dynamically from `get_settings()`.
* **Fallback Defaults**: Optional testing or dev variables must provide safe fallback defaults (e.g., `STATIC_API_KEY: str = "talentsea_secret_api_key_2026"`), while production secrets require `.env` declarations.
* **Typing**: Use strict Pydantic types (`int`, `float`, `str`).

---

## 3. Security Standards & IDOR Prevention

### Insecure Direct Object Reference (IDOR) Rules
- `user_id` MUST NEVER be accepted in request bodies or query parameters for protected resources.
- `user_id` is extracted strictly from the validated JWT Bearer token context (`CurrentAdmin` / `CurrentSubscriber`).
- Every read, update, or delete operation MUST filter by both `resource_id` AND `user_id`:
  ```python
  video = Video.get_or_none((Video.id == video_id) & (Video.user == user_id))
  ```

---

## 4. Indian Standard Time (IST) Guidelines
- Video scheduling and user-facing release timers use **Indian Standard Time (`Asia/Kolkata`, UTC+05:30)**:
  ```python
  from zoneinfo import ZoneInfo
  scheduled_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Kolkata"))
  ```
- Internal audit timestamps (`created_at`, `updated_at`) are saved in UTC.

---

## 5. Peewee Database Connection Lifecycle
- Database connections are opened and closed per HTTP request via `PeeweeDBMiddleware` in `app/middleware/db_middleware.py`.
- Always verify `db_proxy.is_closed()` before calling `db_proxy.connect()` or `db_proxy.close()`.

---

## 6. Resilient Lifespan Background Tasks Pattern

Background tasks (e.g., auto-publisher, subscription expiration, stale guest cleanup) run inside FastAPI `lifespan`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task1 = asyncio.create_task(scheduled_video_auto_publisher())
    task2 = asyncio.create_task(scheduled_subscription_expiration_worker())
    yield
    task1.cancel()
    task2.cancel()
```
* **Error Isolation**: Each worker loop MUST wrap its iteration body in `try...except Exception as e:` so that a single failure or transient network glitch does not kill the long-running worker task.
