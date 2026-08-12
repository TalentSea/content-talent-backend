# Creator OTT & Video Streaming Backend API

A production-grade RESTful API built with **FastAPI**, **Peewee ORM**, **SQLite/PostgreSQL**, and **Bunny.net Cloud Infrastructure** (Bunny Stream, Bunny Storage, and Bunny CDN). Designed following clean architecture principles for video asset management, resumable TUS uploads, webhook state processing, playlist curation, creator profile management, comment moderation, mobile social authentication, guest account upgrades, and real-time watch history playback synchronization.

---

## Architecture and Project Structure

The project strictly follows a **5-Layer Clean Architecture** separating routing, business logic, data access, database models, and cloud utilities:

```
content-talent-backend/
├── app/
│   ├── config.py                 # Pydantic environment configuration
│   ├── database.py               # Peewee database proxy and SQLite initialization
│   ├── dependencies.py           # Authentication dependencies and JWT extraction
│   ├── main.py                   # FastAPI entrypoint, router registration & background workers
│   ├── middleware/               # HTTP Middlewares
│   │   ├── cors_middleware.py    # Cross-Origin Resource Sharing setup
│   │   └── db_middleware.py      # Database connection lifecycle management
│   ├── models/                   # Peewee ORM Entity Definitions
│   │   ├── base.py               # Base model bound to database proxy
│   │   ├── admin.py              # Web Admin Creator profile identity entity
│   │   ├── subscriber.py         # Mobile App Subscriber profile identity entity
│   │   ├── refresh_token.py      # Hashed session refresh tokens entity
│   │   ├── video.py              # Video asset metadata, VideoLike, VideoSave & WatchHistory entities
│   │   ├── playlist.py           # Playlist and junction entities
│   │   └── comment.py            # Comment, thread replies, and junction entities
│   ├── repositories/             # Data Access Layer (Peewee Queries)
│   │   ├── auth_repository.py    # Social & guest subscriber repository with automated stale cleanup
│   │   ├── video_repository.py   # Admin video repository
│   │   ├── mobile_video_repository.py # Mobile catalog, watch history, likes & saves repository
│   │   ├── playlist_repository.py
│   │   ├── profile_repository.py
│   │   └── comment_repository.py
│   ├── routes/                   # FastAPI Endpoint Route Handlers
│   │   ├── webhook_routes.py     # Public Bunny Stream Webhooks (/api/v1/webhooks)
│   │   ├── mobile/               # Mobile Application Endpoints
│   │   │   ├── auth_routes.py    # Mobile Social & Guest Auth (/api/v1/auth)
│   │   │   └── video_routes.py   # Mobile Video Catalog & HLS Player (/api/v1/mobile/videos)
│   │   └── admin/                # Admin Panel Creator Endpoints
│   │       ├── video_routes.py   # Admin Video management endpoints (/api/v1/admin/videos)
│   │       ├── playlist_routes.py# Admin Playlist management endpoints (/api/v1/admin/playlists)
│   │       ├── profile_routes.py # Admin Creator profile & social links (/api/v1/admin/profile)
│   │       └── comment_routes.py # Admin Comment & moderation endpoints (/api/v1/admin/comments)
│   ├── schemas/                  # Pydantic Request/Response DTOs
│   │   ├── auth_schemas.py       # Mobile social login, guest auth & token DTOs
│   │   ├── common_schemas.py     # Generic pagination envelopes
│   │   ├── video_schemas.py      # Admin video request and response DTOs
│   │   ├── mobile_video_schemas.py # Mobile lightweight video feed & streaming DTOs
│   │   ├── playlist_schemas.py   # Playlist DTOs
│   │   ├── profile_schemas.py    # Profile & avatar upload DTOs
│   │   └── comment_schemas.py    # Comment & thread reply DTOs
│   ├── services/                 # Business Logic & Cloud Orchestration
│   │   ├── auth_service.py       # Mobile social login, guest session & JWT token rotation service
│   │   ├── video_service.py      # Admin video orchestration service
│   │   ├── mobile_video_service.py # Mobile video streaming & watch progress service
│   │   ├── playlist_service.py   # Playlist curation service
│   │   ├── profile_service.py    # Profile & Bunny Storage avatar service
│   │   └── comment_service.py    # Comment moderation service
│   └── utils/                    # Cloud Helper Utilities & Cryptography
│       ├── auth.py               # JWT token encoding and decoding
│       ├── social_verifiers.py   # Google OIDC RSA & Facebook Graph API verifiers
│       ├── bunny_client.py       # Bunny REST API HTTP wrappers
│       └── bunny_signature.py    # TUS and HLS presigned token signature helpers
├── docs/                         # Domain Architecture Specifications
│   ├── admin/                    # Creator Admin API Specifications
│   │   ├── video_management_api_specification.md
│   │   ├── playlist_management_api_specification.md
│   │   ├── settings_profile_api_specification.md
│   │   └── comments_management_api_specification.md
│   └── mobile/                   # Mobile Application API Specifications
│       ├── social_authentication_api_specification.md
│       ├── video_streaming_api_specification.md
│       ├── categories_api_specification.md
│       ├── playlists_api_specification.md
│       └── comments_api_specification.md
├── Dockerfile                    # Container image build configuration
├── docker-compose.yml            # Container orchestration specification
├── .env.example                  # Environment configuration template
└── requirements.txt              # Python dependencies specification
```

---

## Technical Features

- **Anonymous Guest Sessions & In-Place Social Account Upgrading**: Hardware-bound `device_id` guest sessions (`POST /api/v1/auth/guest`) allowing users to skip signup on first app launch. When a guest later signs in with Google or Facebook, their existing guest account is upgraded in-place without losing watch history or likes!
- **Watch History & Continue Watching Subsystem**: High-frequency 10-second playback progress synchronization (`POST /videos/{id}/progress`) with auto-resume playback positioning, and paginated `GET /continue-watching` and `GET /history` feeds.
- **Subscriber-Only HLS Streaming & Presigned MP4 Offline Downloads**: Enforces Role-Based Access Control (`get_current_subscriber`) for streaming player metadata and offline download links, while allowing Guest catalog browsing (`get_current_user`).
- **Automated 24-Hour Stale Guest Cleanup Worker**: Configurable background task (`STALE_GUEST_CLEANUP_DAYS=90` in `.env`) running on FastAPI `lifespan` event loop to purge abandoned guest accounts and cascading foreign keys.
- **High-Performance Indexed Popularity Ranking (`popularity_score`)**: Pre-computed B-Tree indexed popularity column (`popularity_score = views + 3*likes`) updated atomically on engagement events for sub-millisecond catalog sorting (`sort=popular`).
- **Resumable TUS Video Uploads**: Computes SHA-256 HMAC presigned signatures allowing client applications to stream video chunks directly to Bunny Stream TUS infrastructure without exposing server credentials.
- **Webhook State Machine**: Handles automated status updates (codes 0–10) sent by Bunny Stream background encoding servers for real-time state tracking (`ENCODING`, `PLAYABLE`, `READY`, `FAILED`, Captions).
- **Dedicated 0-Indexed Thumbnail Management**: Implements dedicated sub-resource upload paths (`slot: 0, 1, 2`) supporting primary cover swaps without accidental asset deletion.
- **Playlist Curation & Deterministic Cover Overrides**: Enables multi-video collection management with deterministic cloud banner overrides (`assets/playlists/pl_{id}_{timestamp}.jpg`).
- **Creator Profile & Bunny CDN Avatar Management**: Manages creator metadata, social links (Twitter, YouTube, Instagram), and avatar photo uploads to Bunny Storage Zone (`assets/avatars/avatar_{id}_{timestamp}.jpg`) with CDN cache-busting URLs.
- **Comments & On-Demand Thread Replies**: Provides high-performance top-level comment listing with `reply_count`, search, video/category filtering, and on-demand paginated reply thread fetching (`GET /comments/{id}/replies?sort=oldest`).
- **Unified `CommentLike` Model**: Manages unique user comment likes/hearts via database-indexed junction table (`comment_likes`).
- **Presigned HLS Stream Security**: Generates time-bound tokenized streaming URLs (`playlist.m3u8?token=...&expires=...`) to prevent unauthorized hotlinking and stream piracy.
- **Standardized Pagination Envelopes**: Wraps list queries inside a generic `PaginatedResponse[T]` structure (`total`, `page`, `limit`, `total_pages`, `items`).
- **Insecure Direct Object Reference (IDOR) Protection**: User identity is strictly derived from validated JWT Bearer tokens.

---

## Getting Started

### Prerequisites

- **Python 3.11+** OR **Docker** and **Docker Compose** installed.

### Environment Setup

Copy `.env.example` to `.env` in the root directory:

```bash
cp .env.example .env
```

Configure your environment settings:

```env
SQLITE_DB_PATH=content-talent.db

# Bunny Stream API Credentials
BUNNY_STREAM_API_KEY=your_bunny_stream_api_key
BUNNY_STREAM_LIBRARY_ID=123456
BUNNY_STREAM_TOKEN_KEY=your_bunny_token_security_key

# Bunny Storage API Credentials
BUNNY_STORAGE_PASSWORD=your_bunny_storage_password
BUNNY_STORAGE_ZONE_NAME=your_storage_zone_name

# Bunny CDN Pull Zone URLs
BUNNY_PULL_ZONE_URL=https://your-pull-zone.b-cdn.net
BUNNY_STORAGE_PULL_ZONE_URL=https://your-storage-pull-zone.b-cdn.net

# JWT Security Settings
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=60
STALE_GUEST_CLEANUP_DAYS=90

# Social Authentication Credentials
GOOGLE_CLIENT_ID=your_google_client_id
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

---

## Running with Docker

Build and launch the application using Docker Compose:

```bash
# Build and start services in container environment
docker-compose up --build -d

# View real-time container logs
docker-compose logs -f web

# Stop container services
docker-compose down
```

Access the interactive API documentation upon startup:
- **Swagger Interactive UI**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/health`

---

## Running Locally

```bash
# 1. Initialize virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Documentation and Standards

Technical specifications and architecture documentation:

- [Mobile Social Authentication Specification](docs/mobile/social_authentication_api_specification.md)
- [Mobile Video Streaming Specification](docs/mobile/video_streaming_api_specification.md)
- [Mobile Categories Specification](docs/mobile/categories_api_specification.md)
- [Video Management API Specification](docs/admin/video_management_api_specification.md)
- [Playlist Management API Specification](docs/admin/playlist_management_api_specification.md)
- [Categories Management API Specification](docs/admin/categories_management_api_specification.md)
- [Settings Profile API Specification](docs/admin/settings_profile_api_specification.md)
- [Comments Management API Specification](docs/admin/comments_management_api_specification.md)
