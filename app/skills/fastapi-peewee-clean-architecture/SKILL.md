---
name: fastapi-peewee-clean-architecture
description: Layered architecture rules for FastAPI + Peewee ORM projects. Enforces Separation of Concerns between Routes, Services, Repositories, Schemas (DTOs), and Models, IDOR security (no user_id in payloads), and SQLite/PostgreSQL connection lifecycle management.
---

# FastAPI + Peewee ORM Clean Architecture Skill

## Overview
This skill documents architectural guidelines, security controls, and design patterns for building modular, maintainable FastAPI applications powered by **Peewee ORM**.

---

## 1. Layered Architecture & Separation of Concerns

The repository enforces strict 5-layer Separation of Concerns:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Routes Layer (app/routes/): HTTP Handlers, Auth & Query Validation       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Services Layer (app/services/): Business Logic & Cloud Orchestration      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Repositories Layer (app/repositories/): Peewee DB CRUD Queries            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Schemas Layer (app/schemas/): Pydantic DTO Validation & JSON Envelopes   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Models Layer (app/models/): Peewee ORM Entities (BaseModel -> db_proxy) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibility Rules
1. **Route Handlers**:
   - MUST NOT execute direct SQL/Peewee ORM queries.
   - MUST validate requests using Pydantic Schemas and inject `get_current_user` dependency.
   - Delegates all business logic to Service classes.
2. **Services Layer**:
   - Executes business rules, cloud API calls (Bunny Stream/Storage), and signature calculations.
   - Calls Repositories for data access.
3. **Repositories Layer**:
   - Encapsulates all Peewee ORM queries (`Model.select()`, `Model.create()`, `model.save()`).
   - Uses `paginate(page, limit)` for pagination queries.

---

## 2. Security Standards & IDOR Prevention

### Insecure Direct Object Reference (IDOR) Rules
- **Rule**: `user_id` MUST NEVER be accepted in request bodies or query parameters for protected resources.
- **Enforcement**: `user_id` is extracted strictly from the validated JWT Bearer token context (`Depends(get_current_user)`).
- **Database Ownership Check**: Every read, update, or delete operation MUST filter by both `resource_id` AND `user_id`:
  ```python
  video = Video.get_or_none((Video.id == video_id) & (Video.user == user_id))
  ```

---

## 3. Peewee Database Connection Lifecycle

- **Database Proxy**: Models inherit from `BaseModel(peewee.Model)` bound to `db_proxy = DatabaseProxy()`.
- **Automatic Connection Management**: Database connections are opened and closed per HTTP request via `PeeweeDBMiddleware` in `app/middleware/db_middleware.py`:
  ```python
  class PeeweeDBMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request, call_next):
          if db_proxy.is_closed():
              db_proxy.connect()
          try:
              response = await call_next(request)
          finally:
              if not db_proxy.is_closed():
                  db_proxy.close()
          return response
  ```

---

## 4. Standardized Pagination Envelope

All list endpoints MUST return items wrapped in the standard `PaginatedResponse[T]` envelope:

```json
{
  "total": 105,
  "page": 1,
  "limit": 20,
  "total_pages": 6,
  "items": [ ... ]
}
```
