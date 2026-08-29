# Creator OTT & Video Streaming Backend API

A production-grade RESTful API built with **FastAPI**, **Peewee ORM**, **SQLite/PostgreSQL**, and **Bunny.net Cloud Infrastructure** (Bunny Stream, Bunny Storage, and Bunny CDN). Designed following clean architecture principles for video asset management, resumable TUS uploads, webhook state processing, playlist curation, categories organization and reordering, creator branding and studio identity, profile management, comment moderation, mobile social authentication, guest account upgrades, and real-time watch history playback synchronization.

---

## Architecture and Project Structure

The project strictly follows a **5-Layer Clean Architecture** separating routing, business logic, data access, database models, and cloud utilities:

```
content-talent-backend/
├── .agents/                      # Team AI Agent Skills & Architecture Playbooks
├── docs/                         # Architecture & API Specifications
│   ├── database_architecture_specification.md # Complete 15-Table Database Schema Specification
│   ├── admin/                    # Admin Portal API Specifications
│   └── mobile/                   # Mobile Application API Specifications
├── app/
│   ├── config.py                 # Pydantic environment configuration and settings
│   ├── database.py               # Peewee database proxy and table initialization
│   ├── dependencies.py           # Authentication dependencies, JWT context and file helpers
│   ├── main.py                   # FastAPI entrypoint, router registration and background workers
│   ├── middleware/               # HTTP Middlewares
│   │   ├── cors_middleware.py    # Cross-Origin Resource Sharing setup
│   │   └── db_middleware.py      # Database connection lifecycle management
│   ├── models/                   # Peewee ORM Entity Definitions
│   │   ├── base.py               # Base model bound to database proxy
│   │   ├── admin.py              # Web Admin Creator profile identity entity
│   │   ├── branding.py           # Public White-Label Studio Branding & Assets entity
│   │   ├── category.py           # Content category and display order entity
│   │   ├── featured_video.py     # Home Screen Featured Carousel curation entity
│   │   ├── subscriber.py         # Mobile App Subscriber profile identity entity
│   │   ├── refresh_token.py      # Hashed session refresh tokens entity
│   │   ├── video.py              # Video asset metadata, VideoLike, VideoSave and WatchHistory entities
│   │   ├── playlist.py           # Playlist and junction entities
│   │   └── comment.py            # Comment, thread replies, and junction entities
│   ├── repositories/             # Data Access Layer (Peewee Queries)
│   │   ├── admin/                # Creator Admin Repositories
│   │   │   ├── video_repository.py
│   │   │   ├── playlist_repository.py
│   │   │   ├── comment_repository.py
│   │   │   ├── profile_repository.py
│   │   │   └── featured_video_repository.py
│   │   ├── mobile/               # Mobile Subscriber Repositories
│   │   │   ├── auth_repository.py
│   │   │   ├── video_repository.py
│   │   │   ├── playlist_repository.py
│   │   │   ├── comment_repository.py
│   │   │   └── featured_video_repository.py
│   │   └── shared/               # Shared Repositories
│   │       ├── branding_repository.py
│   │       └── category_repository.py
│   ├── routes/                   # FastAPI Endpoint Route Handlers
│   │   ├── webhook_routes.py     # Public Bunny Stream Webhooks (/api/v1/webhooks)
│   │   ├── mobile/               # Mobile Application Endpoints
│   │   │   ├── auth_routes.py    # Mobile Social & Guest Auth (/api/v1/auth)
│   │   │   ├── branding_routes.py# Mobile Studio Branding (/api/v1/mobile/branding)
│   │   │   ├── category_routes.py# Mobile Category Catalog (/api/v1/mobile/categories)
│   │   │   ├── comment_routes.py # Mobile Video Comments (/api/v1/mobile)
│   │   │   ├── featured_video_routes.py # Mobile Featured Videos Feed (/api/v1/mobile/featured-videos)
│   │   │   ├── playlist_routes.py# Mobile Public Playlists (/api/v1/mobile/playlists)
│   │   │   └── video_routes.py   # Mobile Video Catalog & HLS Player (/api/v1/mobile/videos)
│   │   └── admin/                # Admin Panel Creator Endpoints
│   │       ├── branding_routes.py# Admin Studio Branding & Customization (/api/v1/admin/branding)
│   │       ├── category_routes.py# Admin Categories & Reordering (/api/v1/admin/categories)
│   │       ├── comment_routes.py # Admin Comment Moderation (/api/v1/admin/comments)
│   │       ├── featured_video_routes.py # Admin Featured Videos Curation (/api/v1/admin/featured-videos)
│   │       ├── playlist_routes.py# Admin Playlist Management (/api/v1/admin/playlists)
│   │       ├── profile_routes.py # Admin Account Profile & Social Links (/api/v1/admin/profile)
│   │       └── video_routes.py   # Admin Video Management & Scheduling (/api/v1/admin/videos)
│   ├── schemas/                  # Pydantic Request/Response DTOs
│   │   ├── admin/                # Creator Admin DTO Schemas
│   │   ├── mobile/               # Mobile Subscriber DTO Schemas
│   │   └── shared/               # Shared DTO Schemas
│   │       ├── common_schemas.py
│   │       ├── branding_schemas.py
│   │       └── category_schemas.py
│   ├── services/                 # Business Logic & Cloud Orchestration
│   │   ├── admin/                # Creator Admin Services
│   │   ├── mobile/               # Mobile Subscriber Services
│   │   └── shared/               # Shared Services
│   │       ├── branding_service.py
│   │       └── category_service.py
│   └── utils/                    # Cloud Helper Utilities & Cryptography
│       ├── auth.py               # JWT token encoding and decoding
│       ├── idp_verifiers.py      # Google OIDC RSA and Facebook Graph API verifiers
│       ├── bunny_client.py       # Bunny REST API HTTP wrappers
│       ├── bunny_signature.py    # TUS and HLS presigned token signature helpers
│       └── image_uploader.py     # Unified cloud image validation and storage engine
├── Dockerfile                    # Container image build configuration
├── docker-compose.yml            # Container orchestration specification
├── .env.example                  # Environment configuration template
└── requirements.txt              # Python dependencies specification
```

---

## Team AI Agent Skills & Standards

The repository contains version-controlled AI Agent Skills in `.agents/skills/` to enforce code quality and architectural standards across the development team:

- **`fastapi-peewee-clean-architecture`**: 5-layer separation of concerns, repository pattern, Pydantic v2 validation contracts, IDOR prevention, and Indian Standard Time (IST / Asia/Kolkata) release scheduling.
- **`bunny-stream-orchestration`**: Bunny Stream container management, HMAC TUS resumable upload signatures, 0-10 status code webhook state machine, and presigned HLS/MP4 security tokens.
- **`cloud-image-uploader`**: Centralized image upload engine (`validate_and_upload_image`), global environment size limits, cache-busting URLs, and automatic cleanup of replaced cloud storage assets.
- **`ott-playlist-curation`**: Playlist lifecycle, ordered junction tables (`PlaylistVideo`), batch drag-and-drop video reordering, and available video pickers.
- **`ott-video-streaming`**: Real-time 10-second watch progress synchronization, auto-resume playback positioning, atomic popularity scoring (`views + 3*likes`), and Subscriber RBAC.
- **`social-and-guest-auth`**: Cryptographic Google OIDC RSA and Facebook Graph API verifiers, hardware-bound guest sessions, seamless in-place account upgrading, and automated 90-day stale guest cleanup workers.

---

## Technical Features

- **Anonymous Guest Sessions and In-Place Social Account Upgrading**: Hardware-bound `device_id` guest sessions (`POST /api/v1/auth/guest`) allowing users to skip signup on first launch. When a guest later signs in with Google or Facebook, their existing guest account is upgraded in-place without losing watch history or likes.
- **Creator Studio Branding and White-Label App Identity**: Dedicated endpoints (`/api/v1/admin/branding`) managing public studio name, tagline, channel description, hero cover banner, and app logo assets, completely separated from personal account settings.
- **Unified Cloud Image Uploader Engine**: Reusable image upload utility enforcing dynamic file size limits and MIME validation (`JPG`, `PNG`, `WebP`, `SVG`), with automatic cloud cleanup of replaced assets to avoid storage bloat.
- **Indian Standard Time (IST / Asia/Kolkata) Video Scheduling**: Native timezone-aware video release scheduling with a background auto-publisher running on an automated loop.
- **Category Organization and Batch Drag-and-Drop Reordering**: Dedicated category management allowing admins to create, update, delete, and reorder category positions using atomic batch updates (`PUT /api/v1/admin/categories/reorder`).
- **Watch History and Continue Watching Subsystem**: High-frequency 10-second playback progress synchronization (`POST /videos/{id}/progress`) with auto-resume playback positioning, and paginated `GET /continue-watching` and `GET /history` feeds.
- **Subscriber-Only HLS Streaming and Presigned MP4 Downloads**: Enforces Role-Based Access Control (`get_current_subscriber`) for streaming player metadata and offline download links, while allowing Guest catalog browsing (`get_current_user`).
- **Automated Stale Guest Cleanup Worker**: Configurable background task (`STALE_GUEST_CLEANUP_DAYS=90`) running on FastAPI lifespan event loop to purge abandoned guest accounts and cascading foreign keys.
- **High-Performance Indexed Popularity Ranking (`popularity_score`)**: Pre-computed B-Tree indexed popularity column (`popularity_score = views + 3*likes`) updated atomically on engagement events for sub-millisecond catalog sorting (`sort=popular`).
- **Resumable TUS Video Uploads**: Computes SHA-256 HMAC presigned signatures allowing client applications to stream video chunks directly to Bunny Stream TUS infrastructure without exposing server credentials.
- **Webhook State Machine**: Handles automated status updates (codes 0-10) sent by Bunny Stream background encoding servers for real-time state tracking (`ENCODING`, `PLAYABLE`, `READY`, `FAILED`, Captions).
- **Dedicated 0-Indexed Thumbnail Management**: Implements dedicated sub-resource upload paths (`slot: 0, 1, 2`) supporting primary cover swaps without accidental asset deletion.
- **Playlist Curation and Deterministic Cover Overrides**: Multi-video collection management with deterministic cloud banner overrides and custom video ordering.
- **Comments and On-Demand Thread Replies**: High-performance top-level comment listing with `reply_count`, search, video/category filtering, and on-demand paginated reply thread fetching (`GET /comments/{id}/replies?sort=oldest`).
- **Presigned HLS Stream Security**: Generates time-bound tokenized streaming URLs (`playlist.m3u8?token=...&expires=...`) to prevent unauthorized hotlinking and stream piracy.
- **Standardized Pagination Envelopes**: Wraps list queries inside a generic `PaginatedResponse[T]` structure (`total`, `page`, `limit`, `total_pages`, `items`).
- **Insecure Direct Object Reference (IDOR) Protection**: User identity is strictly derived from validated JWT Bearer tokens.

---

## API Summary Breakdown (80 Total Endpoints)

- **Admin Endpoints (49)**:
  - Video Management & Scheduling: 11 endpoints
  - Playlist Management: 11 endpoints
  - Category Management & Reordering: 5 endpoints
  - Comment Moderation: 6 endpoints
  - Studio Branding & Customization: 4 endpoints
  - Account Profile & Social Links: 3 endpoints
  - Featured Videos Curation: 3 endpoints
  - Subscription Plans Management: 6 endpoints
- **Mobile Endpoints (30)**:
  - Video Catalog, Player, History, Likes & Saves: 12 endpoints
  - Comments & Replies: 6 endpoints
  - Authentication, Guest & Profiles: 6 endpoints
  - Playlists Catalog: 2 endpoints
  - Category Catalog: 1 endpoint
  - Studio Branding Identity: 1 endpoint
  - Featured Videos Feed: 1 endpoint
  - Subscription Plans Feed: 1 endpoint
- **Webhook Endpoints (1)**:
  - Bunny Stream Transcoding Webhook: 1 endpoint

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
# Database Settings
SQLITE_DB_PATH=content-talent.db

# Bunny Stream API Credentials
BUNNY_STREAM_API_KEY=your_bunny_stream_api_key_here
BUNNY_STREAM_LIBRARY_ID=123456
BUNNY_STREAM_TOKEN_KEY=your_bunny_token_security_key_here

# Bunny Storage API Credentials
BUNNY_STORAGE_PASSWORD=your_bunny_storage_password_here
BUNNY_STORAGE_ZONE_NAME=your_storage_zone_name_here

# Bunny CDN Pull Zone URLs
BUNNY_PULL_ZONE_URL=https://your-stream-pull-zone.b-cdn.net
BUNNY_STORAGE_PULL_ZONE_URL=https://your-storage-pull-zone.b-cdn.net

# JWT Security Settings & Token Expiration
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=60

# Media Presigning & Expiration Timers
BUNNY_TUS_UPLOAD_SIGNATURE_EXPIRE_SECONDS=86400
BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS=7200
BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS=7200

# Background Tasks & Automation Timers
AUTO_PUBLISHER_LOOP_INTERVAL_SECONDS=60
STALE_GUEST_CLEANUP_DAYS=90

# OAuth 2.0 / Social Authentication Providers
GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
FACEBOOK_APP_ID=your_facebook_app_id_here
FACEBOOK_APP_SECRET=your_facebook_app_secret_here

# Image Upload Configuration & Size Limits
ALLOWED_IMAGE_EXTENSIONS=jpg,jpeg,png,webp,svg
MAX_AVATAR_SIZE_MB=2
MAX_THUMBNAIL_SIZE_MB=5
MAX_PLAYLIST_COVER_SIZE_MB=5
MAX_LOGO_SIZE_MB=5
MAX_BANNER_SIZE_MB=10
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
- **ReDoc Interactive UI**: `http://localhost:8000/redoc`
- **Health Check Endpoint**: `http://localhost:8000/health`

---

## Running Locally

```bash
# 1. Initialize virtual environment (if not created yet)
py -m venv .venv

# 2. Activate virtual environment on Windows PowerShell:
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch development server with hot-reload:
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Documentation and Standards

Technical specifications and architecture documentation:

### 🏛️ Database Architecture
- [Complete 15-Table Database Schema Specification](docs/database_architecture_specification.md)

### 💻 Admin Web Portal API Specifications
- [Branding Management API Specification](docs/admin/branding_management_api_specification.md)
- [Video Management API Specification](docs/admin/video_management_api_specification.md)
- [Playlist Management API Specification](docs/admin/playlist_management_api_specification.md)
- [Categories Management API Specification](docs/admin/categories_management_api_specification.md)
- [Featured Videos Management API Specification](docs/admin/featured_videos_management_api_specification.md)
- [Settings Profile API Specification](docs/admin/settings_profile_api_specification.md)
- [Comments Management API Specification](docs/admin/comments_management_api_specification.md)
- [Subscription Plans Management API Specification](docs/admin/subscription_plans_management_api_specification.md)

### 📱 Mobile Application API Specifications
- [Mobile Social Authentication Specification](docs/mobile/social_authentication_api_specification.md)
- [Mobile Branding Specification](docs/mobile/branding_api_specification.md)
- [Mobile Video Streaming Specification](docs/mobile/video_streaming_api_specification.md)
- [Mobile Categories Specification](docs/mobile/categories_api_specification.md)
- [Mobile Playlists Specification](docs/mobile/playlists_api_specification.md)
- [Mobile Comments Specification](docs/mobile/comments_api_specification.md)
- [Mobile Featured Videos Specification](docs/mobile/featured_videos_api_specification.md)
- [Mobile Subscription Plans Specification](docs/mobile/subscription_plans_api_specification.md)
