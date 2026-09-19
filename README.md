# Creator OTT & Video Streaming Backend API

A production-grade RESTful API built with **FastAPI**, **Peewee ORM**, **PostgreSQL**, and **Bunny.net Cloud Infrastructure** (Bunny Stream, Bunny Storage, and Bunny CDN). Designed following clean architecture principles for video asset management, resumable TUS uploads, webhook state processing, playlist curation, categories organization and reordering, creator branding and studio identity, profile management, comment moderation, mobile social authentication, guest account upgrades, and real-time watch history playback synchronization.

---

## Architecture and Project Structure

The project strictly follows a **5-Layer Clean Architecture** separating routing, business logic, data access, database models, and cloud utilities:

```
content-talent-backend/
├── .agents/                      # Team AI Agent Skills & Architecture Playbooks
├── docs/                         # Architecture & API Specifications
│   ├── mobile/                   # Mobile Application API Specifications
│   ├── admin/                    # Admin Portal API Specifications
│   ├── database_architecture_specification.md # Complete 23-Table Database Schema Specification
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
│   │   ├── subscription_plan.py  # Creator Subscription Plans, Pricing and Counter Cache entity
│   │   ├── user_subscription.py  # Active subscriber membership entitlements & validity entity
│   │   ├── payment.py            # Razorpay orders and payment transactions ledger entity
│   │   ├── refresh_token.py      # Hashed session refresh tokens entity
│   │   ├── video.py              # Video asset metadata, VideoLike, VideoSave, WatchHistory, and VideoViewEvent entities
│   │   ├── playlist.py           # Playlist, PlaylistVideo, and PlaylistSave entities
│   │   ├── comment.py            # Comment, thread replies, and junction entities
│   │   └── ad_monetization.py    # AdImpressionEvent, AdPlatformMonthlyReconciliation, AdMonthlySettlement, and CreatorPayoutProfile entities
│   ├── repositories/             # Data Access Layer (Peewee Queries)
│   │   ├── admin/                # Creator Admin Repositories
│   │   │   ├── auth_repository.py
│   │   │   ├── dashboard_repository.py
│   │   │   ├── video_repository.py
│   │   │   ├── playlist_repository.py
│   │   │   ├── comment_repository.py
│   │   │   ├── profile_repository.py
│   │   │   ├── featured_video_repository.py
│   │   │   ├── subscription_plan_repository.py
│   │   │   └── monetization_repository.py
│   │   ├── mobile/               # Mobile Subscriber Repositories
│   │   │   ├── auth_repository.py
│   │   │   ├── video_repository.py
│   │   │   ├── playlist_repository.py
│   │   │   ├── comment_repository.py
│   │   │   ├── featured_video_repository.py
│   │   │   ├── subscription_plan_repository.py
│   │   │   ├── user_subscription_repository.py
│   │   │   └── payment_repository.py
│   │   └── shared/               # Shared Repositories
│   │       ├── branding_repository.py
│   │       └── category_repository.py
│   ├── routes/                   # FastAPI Endpoint Route Handlers
│   │   ├── webhook_routes.py     # Bunny Stream & Razorpay Webhooks (/api/v1/webhooks)
│   │   ├── mobile/               # Mobile Application Endpoints
│   │   │   ├── auth_routes.py    # Mobile Social & Guest Auth (/api/v1/auth)
│   │   │   ├── branding_routes.py# Mobile Studio Branding (/api/v1/mobile/branding)
│   │   │   ├── category_routes.py# Mobile Category Catalog (/api/v1/mobile/categories)
│   │   │   ├── comment_routes.py # Mobile Video Comments (/api/v1/mobile)
│   │   │   ├── featured_video_routes.py # Mobile Featured Videos Feed (/api/v1/mobile/featured-videos)
│   │   │   ├── payment_routes.py # Mobile Razorpay Orders & Verification (/api/v1/mobile/payments)
│   │   │   ├── subscription_routes.py # Mobile Active Entitlements Status (/api/v1/mobile/subscriptions)
│   │   │   ├── playlist_routes.py# Mobile Public Playlists (/api/v1/mobile/playlists)
│   │   │   ├── subscription_plan_routes.py # Mobile Subscription Plans (/api/v1/mobile/plans)
│   │   │   └── video_routes.py   # Mobile Video Catalog, HLS Player & Ad Impression Telemetry (/api/v1/mobile/videos)
│   │   └── admin/                # Admin Panel Creator Endpoints
│   │       ├── auth_routes.py    # Admin Authentication & Token Lifecycle (/api/v1/admin/auth)
│   │       ├── dashboard_routes.py# Admin Studio Dashboard & Analytics (/api/v1/admin/dashboard)
│   │       ├── branding_routes.py# Admin Studio Branding & Customization (/api/v1/admin/branding)
│   │       ├── category_routes.py# Admin Categories & Reordering (/api/v1/admin/categories)
│   │       ├── comment_routes.py # Admin Comment Moderation (/api/v1/admin/comments)
│   │       ├── featured_video_routes.py # Admin Featured Videos Curation (/api/v1/admin/featured-videos)
│   │       ├── playlist_routes.py# Admin Playlist Management (/api/v1/admin/playlists)
│   │       ├── profile_routes.py # Admin Account Profile & Social Links (/api/v1/admin/profile)
│   │       ├── subscription_plan_routes.py # Admin Subscription Plans Management (/api/v1/admin/plans)
│   │       ├── monetization_routes.py # Admin Ad Monetization, Analytics & Payout Settings (/api/v1/admin/monetization)
│   │       └── video_routes.py   # Admin Video Management & Scheduling (/api/v1/admin/videos)
│   ├── schemas/                  # Pydantic Request/Response DTOs
│   │   ├── admin/                # Creator Admin DTO Schemas
│   │   │   ├── auth_schemas.py
│   │   │   ├── dashboard_schemas.py
│   │   │   ├── video_schemas.py
│   │   │   ├── playlist_schemas.py
│   │   │   ├── category_schemas.py
│   │   │   ├── comment_schemas.py
│   │   │   ├── profile_schemas.py
│   │   │   ├── featured_video_schemas.py
│   │   │   ├── subscription_plan_schemas.py
│   │   │   └── monetization_schemas.py
│   │   ├── mobile/               # Mobile Subscriber DTO Schemas
│   │   │   ├── auth_schemas.py
│   │   │   ├── video_schemas.py
│   │   │   ├── playlist_schemas.py
│   │   │   ├── category_schemas.py
│   │   │   ├── comment_schemas.py
│   │   │   ├── featured_video_schemas.py
│   │   │   ├── subscription_plan_schemas.py
│   │   │   └── payment_schemas.py
│   │   └── shared/               # Shared DTO Schemas
│   │       ├── common_schemas.py
│   │       ├── branding_schemas.py
│   │       └── category_schemas.py
│   ├── scripts/                  # Administrative Automation & CLI Utilities
│   │   ├── create_creator.py     # Atomic Creator Admin, Studio Branding & Plans Onboarding CLI
│   │   ├── manage_creator_status.py # Creator Account Status & Suspension Management CLI
│   │   └── reconcile_monthly_ads.py # Platform Ad Revenue Settlement & Monthly Payouts Reconciliation CLI
│   ├── services/                 # Business Logic & Cloud Orchestration
│   │   ├── admin/                # Creator Admin Services
│   │   │   ├── auth_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── video_service.py
│   │   │   ├── playlist_service.py
│   │   │   ├── comment_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── featured_video_service.py
│   │   │   ├── subscription_plan_service.py
│   │   │   └── monetization_service.py
│   │   ├── mobile/               # Mobile Subscriber Services
│   │   │   ├── auth_service.py
│   │   │   ├── video_service.py
│   │   │   ├── playlist_service.py
│   │   │   ├── comment_service.py
│   │   │   ├── featured_video_service.py
│   │   │   ├── subscription_plan_service.py
│   │   │   └── payment_service.py
│   │   └── shared/               # Shared Services
│   │       ├── branding_service.py
│   │       └── category_service.py
│   └── utils/                    # Cloud Helper Utilities & Cryptography
│       ├── auth.py               # PBKDF2 password hashing & JWT token encoding/decoding
│       ├── date_utils.py         # Centralized platform timezone resolution (APP_TIMEZONE) & UTC standard
│       ├── idp_verifiers.py      # Google OIDC RSA and Facebook Graph API verifiers
│       ├── bunny_client.py       # Bunny REST API HTTP wrappers
│       ├── bunny_signature.py    # TUS and HLS presigned token signature helpers
│       ├── image_uploader.py     # Unified cloud image validation and storage engine
│       └── razorpay_client.py    # Razorpay REST API orders & HMAC cryptographic verifier
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

- **Creator Admin Authentication & Dual-Token Session Architecture**: Secure admin identity lifecycle (`/api/v1/admin/auth/*`) enforcing in-memory 30-minute access tokens and 60-day `HttpOnly; Secure; SameSite=Strict` refresh cookies. Features NIST SP 800-132 PBKDF2-HMAC-SHA256 password hashing (600,000 iterations), single-use refresh token rotation, non-destructive multi-device session isolation (ensuring a stale device attempting refresh never disrupts an active session on a newer device), and session profile rehydration (`GET /me`).
- **Atomic Creator Studio Onboarding CLI**: Zero public registration architecture (`/register` eliminated for anti-abuse). Internal operator CLI (`app.scripts.create_creator`) that atomically provisions the `Admin` user, 1:1 `Branding` studio identity, and two mandatory subscription tiers (`with_ads` and `no_ads`) within a single database transaction.
- **Creator Studio Dashboard & Real-Time Analytics Subsystem**: Multi-widget studio analytics engine featuring high-level KPI overview cards with period-over-period growth telemetry (`GET /api/v1/admin/dashboard/stats`), dynamic chronological time-series area charts (`GET /api/v1/admin/dashboard/analytics`) with auto-interval grouping (day/week/month), subscription tier distribution (`GET /api/v1/admin/dashboard/subscription-breakdown`) with actual period revenue and subscriber shares, and a paginated recent members feed (`GET /api/v1/admin/dashboard/recent-activity`) with audience segmentation (`all`, `subscribers`, `users`), strictly excluding anonymous guests.
- **Immutable View Telemetry & Zero-Trust Anti-Spam Gatekeeper**: Dedicated append-only `video_view_events` ledger decoupled from mutable user watch history, ensuring creator view analytics remain permanent and tamper-proof even when subscribers purge personal history. Enforces strict server-side 30% watch threshold verification against `watch_history`, 30-minute continuous session debouncing, rolling 24-hour daily capping (max 3 views/day), and strict subscriber-only role validation.
- **Razorpay Payment Gateway & Cryptographic Signature Verification**: Production-grade monetization engine featuring order initialization (`POST /api/v1/mobile/payments/create-order`), SHA-256 HMAC cryptographic signature verification (`POST /api/v1/mobile/payments/verify`), atomic database transaction commits with automatic rollback on failure, idempotent entitlement activation, and an asynchronous fallback webhook listener (`POST /api/v1/webhooks/razorpay`).
- **Two-Pillar Subscription Expiration Architecture**: Real-time Just-In-Time (JIT) lazy expiration checks on subscriber requests paired with an automated background task (`scheduled_subscription_expiration_worker`) on the FastAPI lifespan event loop to systematically expire outdated memberships.
- **Single-Query Hero Carousel Curation (`likes_count` Subquery)**: Ultra-optimized home screen featured video carousel mapping (`GET /api/v1/mobile/featured-videos`) fetching video metadata, subscriber engagement flags (`is_liked`, `is_saved`), and real-time total likes count via correlated SQL scalar subqueries in 1 single database roundtrip with zero N+1 query overhead.
- **Subscription Plans & Monetization Tier Management**: Standardized Two-Tier OTT monetization architecture (Tier 1: with-ads and Tier 2: no-ads) with platform-governed technical feature checklists (`app.constants.plans`), admin endpoints (`GET /api/v1/admin/plans` and `PUT /api/v1/admin/plans/{id}`) for pricing, discount %, and custom copy, mobile paywall checkout feed (`GET /api/v1/mobile/plans`), and counter cache columns for sub-millisecond reads.
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
- **Creator Ad Monetization, Settlements Engine & Dynamic eCPM Architecture**: Comprehensive advertising telemetry and monthly revenue settlement engine. Dispatches Google IMA VAST beacons (`POST /api/v1/mobile/videos/{id}/ad-impression`) with configurable rapid-fire anti-spam debouncing and rolling session caps. Implements a 30% white-label platform technology commission deducted strictly at the eCPM layer ($\text{Creator eCPM} = \text{Raw eCPM} \times 0.70$) without exposing internal margins on creator APIs. Features dynamic historical eCPM baselines (zero hardcoded rates), ₹500 minimum payout threshold rollovers, bank payout profiles with masked account numbers and auto-resolved IFSC codes, and a dedicated back-office reconciliation CLI (`reconcile_monthly_ads.py`).
- **Standardized Pagination Envelopes**: Wraps list queries inside a generic `PaginatedResponse[T]` structure (`total`, `page`, `limit`, `total_pages`, `items`).
- **Insecure Direct Object Reference (IDOR) Protection**: User identity is strictly derived from validated JWT Bearer tokens.

---

## API Summary Breakdown (94 Total Endpoints)

- **Admin Endpoints (58)**:
  - Creator Authentication & Session Lifecycle: 4 endpoints
  - Studio Dashboard & Analytics: 4 endpoints
  - Video Management & Scheduling: 11 endpoints
  - Playlist Management: 11 endpoints
  - Category Management & Reordering: 5 endpoints
  - Comment Moderation: 6 endpoints
  - Studio Branding & Customization: 4 endpoints
  - Account Profile & Social Links: 3 endpoints
  - Featured Videos Curation: 3 endpoints
  - Subscription Plans Management: 2 endpoints
  - Ad Monetization, Analytics, Payout Settings & Statements: 5 endpoints
- **Mobile Endpoints (36)**:
  - Video Catalog, Player, History, Likes, Saves & Ad Telemetry: 13 endpoints
  - Comments & Replies: 6 endpoints
  - Authentication, Guest & Profiles: 6 endpoints
  - Razorpay Orders & Verification: 2 endpoints
  - Subscription Entitlement Status: 1 endpoint
  - Playlists Catalog & Bookmarks: 4 endpoints
  - Category Catalog: 1 endpoint
  - Studio Branding Identity: 1 endpoint
  - Featured Videos Feed: 1 endpoint
  - Subscription Plans Feed: 1 endpoint
- **Webhook Endpoints (2)**:
  - Bunny Stream Transcoding Webhook: 1 endpoint
  - Razorpay Payment Webhook: 1 endpoint

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
DATABASE_URL=postgresql://user:password@localhost:5432/content_talent_db

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
SUBSCRIPTION_EXPIRATION_LOOP_INTERVAL_SECONDS=3600
MAX_FEATURED_VIDEOS_PER_CREATOR=10

# Razorpay Payment Gateway Credentials & Webhooks
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret

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

# Video Playback, Anti-Spam Telemetry & Decision Parameters
VIDEO_VIEW_WATCH_THRESHOLD_PERCENT=30.0
VIDEO_VIEW_COOLDOWN_MINUTES=30
VIDEO_VIEW_MAX_DAILY_PER_USER=3
VIDEO_VIEW_DAILY_WINDOW_HOURS=24
VIDEO_COMPLETION_THRESHOLD_PERCENT=95.0
CONTINUE_WATCHING_MIN_SECONDS=10
POPULARITY_SCORE_LIKE_WEIGHT=3

# Video Ad Monetization (Google IMA / VAST & Monthly Settlements)
GOOGLE_IMA_VAST_TAG_URL=https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_preroll_skippable&sz=640x480&ciu_szs=300x250%2C728x90&gdfp_req=1&output=vast&unviewed_position_start=1&env=vp&impl=s&correlator=
PLATFORM_AD_COMMISSION_PERCENT=30.0
PAYOUT_DAY_OF_MONTH=28
MIN_PAYOUT_THRESHOLD=500.0
AD_IMPRESSION_DEBOUNCE_SECONDS=10
AD_IMPRESSION_SESSION_WINDOW_MINUTES=30
AD_IMPRESSION_MAX_PER_SESSION=10

# Platform & Content Defaults
APP_TIMEZONE=Asia/Kolkata
DEFAULT_CURRENCY=INR
DEFAULT_CATEGORY_COLOR=#3b82f6
```

---

## 🚀 Creator Onboarding & Setup (Provisioning CLI)

The platform operates as a specialized **White-Labeled Creator OTT Platform**. To eliminate bot account creation, orphaned tenant database records, and credential stuffing attacks, there is intentionally **zero public sign-up (`/register`)** on the Creator Admin portal.

Instead, platform administrators provision verified creator accounts atomically using the internal CLI onboarding utility (`app.scripts.create_creator`):

```bash
# Option A: Direct provisioning with command-line arguments:
python -m app.scripts.create_creator \
    --email creator@studio.com \
    --password "SecureSecretPass123!" \
    --first-name "John" \
    --last-name "Doe" \
    --studio-name "John Doe Studio"

# Option B: Secure interactive execution (password prompted with hidden terminal input):
python -m app.scripts.create_creator --email creator@studio.com --studio-name "John Doe Studio"
# Prompt: Enter creator password (min 8 chars): [hidden]
# Prompt: Confirm creator password: [hidden]
```

### CLI Arguments Reference

| Argument        |  Type  | Required | Description                                                                                                      |
| :-------------- | :----: | :------: | :--------------------------------------------------------------------------------------------------------------- |
| `--email`       | String | **Yes**  | Creator's primary login email address (case-insensitive, trimmed).                                               |
| `--password`    | String | **Yes**  | Initial login password (minimum 8 characters). If omitted, prompts interactively via `getpass`.                  |
| `--first-name`  | String |    No    | Creator's first name.                                                                                            |
| `--last-name`   | String |    No    | Creator's last name.                                                                                             |
| `--studio-name` | String |    No    | Public channel / OTT studio brand name (defaults to `f"{first_name} {last_name} Studio"` or `"Creator Studio"`). |

### 🔒 Atomic Provisioning Invariants

Every onboarding execution runs inside a single database transaction (`with db_proxy.atomic():`):

1. **Admin Account**: Created with NIST SP 800-132 compliant PBKDF2-HMAC-SHA256 password hashing (600,000 iterations, 16-byte random salt).
2. **1:1 Studio Identity (`Branding`)**: Immediately binds a branding record with `studio_name`, ensuring mobile app subscribers and the web admin shell never encounter `null` studio references or 404 errors.
3. **Two Fixed Subscription Tiers (`SubscriptionPlan`)**:
   - **Plan 1 (`Standard with Ads`)**: ₹99/month (`base_price=99.0`, `features=["Full video catalog access", "Standard definition streaming", "Occasional short advertisements"]`).
   - **Plan 2 (`Premium Ad-Free`)**: ₹199/month (`base_price=199.0`, `features=["100% Ad-free streaming", "Ultra HD resolution", "Offline mobile downloads", "Early access to original releases"]`).

---

## 💰 Ad Revenue Monthly Settlement & Reconciliation CLI

Platform administrators execute monthly advertising revenue settlements and bank wire disbursements using the dedicated back-office reconciliation CLI (`app.scripts.reconcile_monthly_ads`).

### 1. Execute Monthly Reconciliation (By Gross Revenue or Fixed eCPM)
```bash
# Reconcile month by entering total gross revenue from Google Ad Manager:
python -m app.scripts.reconcile_monthly_ads --month 2026-09 --revenue 75000.0

# Or reconcile month by entering a fixed gross eCPM rate:
python -m app.scripts.reconcile_monthly_ads --month 2026-09 --ecpm 180.0

# Bypass interactive confirmation prompt (for automation scripts):
python -m app.scripts.reconcile_monthly_ads --month 2026-09 --revenue 75000.0 --yes
```

### 2. Confirm Bank Wire Transfer (Mark Paid with Bank UTR)
Once wire transfers are dispatched on the 28th, confirm the disbursement by linking the official bank UTR code to the creator's itemized statement:
```bash
python -m app.scripts.reconcile_monthly_ads --mark-paid STMT-202609-ADM42-8F9B --utr HDFC20261028994820
```

> **How Creator Identification Works (`1 Transaction ➔ 1 Creator`):**  
> Every statement ID follows the deterministic pattern: `STMT-{YYYYMM}-ADM{creator_id}-{hash}` (e.g. `ADM42` = Creator Admin ID `42`). In the database, each statement record is uniquely bound to one specific creator via `creator_id`. Marking a statement as paid directly attributes the bank UTR to that exact creator's settlement statement.

### 3. Review Master Platform Audit Ledger
```bash
python -m app.scripts.reconcile_monthly_ads --history
```

---

## 🛡️ Creator Account Status & Suspension Management CLI

Platform administrators can list, deactivate, reactivate, or inspect creator accounts using `app.scripts.manage_creator_status`:

### 1. List All Creator Accounts
```bash
python -m app.scripts.manage_creator_status list
```

### 2. Deactivate a Creator Account
Suspends the creator, sets `is_active = False`, invalidates active web/mobile refresh sessions immediately, and disables ad monetization telemetry:
```bash
# Deactivate by email:
python -m app.scripts.manage_creator_status deactivate --email creator@example.com --reason "Terms violation"

# Or deactivate by numeric ID:
python -m app.scripts.manage_creator_status deactivate --id 3 --reason "Contract termination"
```

### 3. Reactivate a Creator Account
Restores login access and ad impression accumulation:
```bash
python -m app.scripts.manage_creator_status activate --email creator@example.com
```

### 4. Inspect Detailed Creator Account Status
```bash
python -m app.scripts.manage_creator_status status --id 3
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

- **Swagger Interactive UI**: `http://138.68.140.83:8000/docs`
- **ReDoc Interactive UI**: `http://138.68.140.83:8000/redoc`
- **Health Check Endpoint**: `http://138.68.140.83:8000/health`

---

## Running Locally

```bash
# 1. Initialize virtual environment (if not created yet)
py -m venv .venv

# 2. Activate virtual environment on Windows PowerShell:
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Atomically provision initial Creator Admin account:
python -m app.scripts.create_creator --email creator@studio.com --password "SecureSecret123!" --studio-name "Creator Studio"

# 5. Launch development server with hot-reload:
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Documentation and Standards

Technical specifications and architecture documentation:

### 🏛️ Database Architecture

- [Complete 23-Table Database Schema Specification](docs/database_architecture_specification.md)

### 💻 Admin Web Portal API Specifications

- [Creator Admin Authentication & Identity Lifecycle API Specification](docs/admin/admin_authentication_api_specification.md)
- [Studio Dashboard & Analytics API Specification](docs/admin/dashboard_analytics_api_specification.md)
- [Branding Management API Specification](docs/admin/branding_management_api_specification.md)
- [Video Management API Specification](docs/admin/video_management_api_specification.md)
- [Playlist Management API Specification](docs/admin/playlist_management_api_specification.md)
- [Categories Management API Specification](docs/admin/categories_management_api_specification.md)
- [Featured Videos Management API Specification](docs/admin/featured_videos_management_api_specification.md)
- [Settings Profile API Specification](docs/admin/settings_profile_api_specification.md)
- [Comments Management API Specification](docs/admin/comments_management_api_specification.md)
- [Subscription Plans Management API Specification](docs/admin/subscription_plans_management_api_specification.md)
- [Creator Ad Monetization, Settlements & Bank Payout Settings API Specification](docs/admin/ad_monetization_management_api_specification.md)

### 📱 Mobile Application API Specifications

- [Mobile Social Authentication Specification](docs/mobile/social_authentication_api_specification.md)
- [Mobile Branding Specification](docs/mobile/branding_api_specification.md)
- [Mobile Video Streaming Specification](docs/mobile/video_streaming_api_specification.md)
- [Mobile Categories Specification](docs/mobile/categories_api_specification.md)
- [Mobile Playlists Specification](docs/mobile/playlists_api_specification.md)
- [Mobile Comments Specification](docs/mobile/comments_api_specification.md)
- [Mobile Featured Videos Specification](docs/mobile/featured_videos_api_specification.md)
- [Mobile Subscription Plans Specification](docs/mobile/subscription_plans_api_specification.md)
- [Mobile Razorpay Payment & Subscriptions Specification](docs/mobile/razorpay_payment_subscriptions_api_specification.md)
