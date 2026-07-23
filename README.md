# Creator OTT & Video Streaming Backend API

A production-grade RESTful API built with **FastAPI**, **Peewee ORM**, **SQLite**, and **Bunny.net Cloud Infrastructure** (Bunny Stream, Bunny Storage, and Bunny CDN). Designed following clean architecture principles for video asset management, resumable TUS uploads, webhook state processing, and playlist curation.

---

## Architecture and Project Structure

The project strictly follows a **5-Layer Clean Architecture** separating routing, business logic, data access, database models, and cloud utilities:

```
content-talent-backend/
├── app/
│   ├── config.py                 # Pydantic environment configuration
│   ├── database.py               # Peewee database proxy and SQLite initialization
│   ├── dependencies.py           # Authentication dependencies and JWT extraction
│   ├── main.py                   # FastAPI entrypoint and global middleware registration
│   ├── middleware/               # HTTP Middlewares
│   │   ├── cors_middleware.py    # Cross-Origin Resource Sharing setup
│   │   └── db_middleware.py      # Database connection lifecycle management
│   ├── models/                   # Peewee ORM Entity Definitions
│   │   ├── base.py               # Base model bound to database proxy
│   │   ├── user.py               # User authentication entity
│   │   ├── video.py              # Video asset metadata entity
│   │   └── playlist.py           # Playlist and junction entities
│   ├── repositories/             # Data Access Layer (Peewee Queries)
│   │   ├── video_repository.py
│   │   └── playlist_repository.py
│   ├── routes/                   # FastAPI Endpoint Route Handlers
│   │   ├── video_routes.py       # Video lifecycle endpoints
│   │   └── playlist_routes.py    # Playlist management endpoints
│   ├── schemas/                  # Pydantic Request/Response DTOs
│   │   ├── common_schemas.py     # Generic pagination envelopes
│   │   ├── video_schemas.py      # Video request and response DTOs
│   │   └── playlist_schemas.py   # Playlist DTOs
│   ├── services/                 # Business Logic & Cloud Orchestration
│   │   ├── video_service.py      # Video orchestration service
│   │   └── playlist_service.py   # Playlist curation service
│   ├── skills/                   # Standard Operating Procedures & Skill Docs
│   │   ├── bunny-stream-orchestration/
│   │   ├── fastapi-peewee-clean-architecture/
│   │   └── ott-playlist-curation/
│   └── utils/                    # Cloud Helper Utilities & Cryptography
│       ├── auth.py               # JWT token encoding and decoding
│       ├── bunny_client.py       # Bunny REST API HTTP wrappers
│       └── bunny_signature.py    # TUS and HLS presigned token signature helpers
├── docs/                         # Domain Architecture Specifications
│   ├── video_management_api_specification.md
│   ├── playlist_management_api_specification.md
│   └── backend_architecture_blueprint.md
├── Dockerfile                    # Container image build configuration
├── docker-compose.yml            # Container orchestration specification
├── .env.example                  # Environment configuration template
└── requirements.txt              # Python dependencies specification
```

---

## Technical Features

- **Resumable TUS Video Uploads**: Computes SHA-256 HMAC presigned signatures allowing client applications to stream video chunks directly to Bunny Stream TUS infrastructure without exposing server credentials.
- **Webhook State Machine**: Handles automated status updates (codes 0–10) sent by Bunny Stream background encoding servers for real-time state tracking (`ENCODING`, `PLAYABLE`, `READY`, `FAILED`, Captions).
- **Dedicated 0-Indexed Thumbnail Management**: Implements dedicated sub-resource upload paths (`slot: 0, 1, 2`) supporting primary cover swaps without accidental asset deletion.
- **Playlist Curation & Deterministic Cover Overrides**: Enables multi-video collection management with deterministic cloud banner overrides (`assets/playlists/playlist_{id}.jpg`).
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
SQLITE_DB_PATH=ott_platform.db
BUNNY_STREAM_API_KEY=your_bunny_stream_api_key
BUNNY_STREAM_LIBRARY_ID=123456
BUNNY_STREAM_TOKEN_KEY=your_bunny_token_security_key
BUNNY_STORAGE_PASSWORD=your_bunny_storage_password
BUNNY_STORAGE_ZONE_NAME=your_storage_zone_name
BUNNY_PULL_ZONE_URL=https://your-pull-zone.b-cdn.net
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
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

- [Video Management API Specification](docs/video_management_api_specification.md)
- [Playlist Management API Specification](docs/playlist_management_api_specification.md)
- [Backend Architecture Blueprint](docs/backend_architecture_blueprint.md)

Standard operating procedures:

- [Bunny Stream Orchestration Skill](app/skills/bunny-stream-orchestration/SKILL.md)
- [FastAPI and Peewee Clean Architecture Skill](app/skills/fastapi-peewee-clean-architecture/SKILL.md)
- [OTT Playlist Curation Skill](app/skills/ott-playlist-curation/SKILL.md)
