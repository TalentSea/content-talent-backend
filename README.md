# Creator OTT & Video Streaming Backend API

A production-grade RESTful API built with **FastAPI**, **Peewee ORM**, **SQLite**, and **Bunny.net Cloud Infrastructure** (Bunny Stream, Bunny Storage, and Bunny CDN). Designed following clean architecture principles for video asset management, resumable TUS uploads, webhook state processing, playlist curation, categories organization and reordering, creator branding and studio identity, profile management, comment moderation, mobile social authentication, guest account upgrades, and real-time watch history playback synchronization.

---

## Architecture and Project Structure

The project strictly follows a **5-Layer Clean Architecture** separating routing, business logic, data access, database models, and cloud utilities:

```
content-talent-backend/
├── .agents/                      # Team AI Agent Skills & Architecture Playbooks
├── docs/                         # Architecture & API Specifications
│   ├── mobile/                   # Mobile Application API Specifications
│   ├── admin/                    # Admin Portal API Specifications
│   ├── database_architecture_specification.md # Complete 24-Table Database Schema Specification
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
│   │   ├── tenant.py             # Tenant organization, white-label branding & app identity entity
│   │   ├── admin.py              # Platform Super Admin & Tenant Admin profile entity
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
│   │   ├── verification_code.py  # Temporary OTP verification codes for registration and password reset
│   │   └── ad_monetization.py    # AdImpressionEvent, AdPlatformMonthlyReconciliation, AdMonthlySettlement, and CreatorPayoutProfile entities
│   ├── repositories/             # Data Access Layer (Peewee Queries)
│   │   ├── admin/                # Creator Admin Repositories
│   │   │   ├── auth_repository.py
│   │   │   ├── tenant_repository.py
│   │   │   ├── dashboard_repository.py
│   │   │   ├── video_repository.py
│   │   │   ├── playlist_repository.py
│   │   │   ├── comment_repository.py
│   │   │   ├── profile_repository.py
│   │   │   ├── featured_video_repository.py
│   │   │   ├── subscription_plan_repository.py
│   │   │   ├── monetization_repository.py
│   │   │   └── super_admin_monetization_repository.py
│   │   ├── mobile/               # Mobile Subscriber Repositories
│   │   │   ├── auth_repository.py
│   │   │   ├── verification_repository.py
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
│   │   │   └── video_routes.py   # Mobile Video Catalog, Shorts Swipe Feed, HLS Player & Ad Impression Telemetry (/api/v1/mobile/videos)
│   │   └── admin/                # Admin Panel Creator Endpoints
│   │       ├── auth_routes.py    # Admin Authentication & Token Lifecycle (/api/v1/admin/auth)
│   │       ├── tenant_routes.py  # Super Admin Tenant Management (/api/v1/admin/tenants)
│   │       ├── admin_user_routes.py # Tenant Staff Admin User Management (/api/v1/admin/users)
│   │       ├── dashboard_routes.py# Admin Studio Dashboard & Analytics (/api/v1/admin/dashboard)
│   │       ├── branding_routes.py# Admin Studio Branding & Customization (/api/v1/admin/branding)
│   │       ├── category_routes.py# Admin Categories & Reordering (/api/v1/admin/categories)
│   │       ├── comment_routes.py # Admin Comment Moderation (/api/v1/admin/comments)
│   │       ├── featured_video_routes.py # Admin Featured Videos Curation (/api/v1/admin/featured-videos)
│   │       ├── playlist_routes.py# Admin Playlist Management (/api/v1/admin/playlists)
│   │       ├── profile_routes.py # Admin Account Profile & Social Links (/api/v1/admin/profile)
│   │       ├── subscription_plan_routes.py # Admin Subscription Plans Management (/api/v1/admin/plans)
│   │       ├── monetization_routes.py # Admin Ad Monetization, Analytics & Payout Settings (/api/v1/admin/monetization)
│   │       ├── super_admin_monetization_routes.py # Super Admin Ad Reconciliation & Settlements (/api/v1/admin/monetization)
│   │       └── video_routes.py   # Admin Video Management & Scheduling (/api/v1/admin/videos)
│   ├── schemas/                  # Pydantic Request/Response DTOs
│   │   ├── admin/                # Creator Admin DTO Schemas
│   │   │   ├── auth_schemas.py
│   │   │   ├── tenant_schemas.py
│   │   │   ├── dashboard_schemas.py
│   │   │   ├── video_schemas.py
│   │   │   ├── playlist_schemas.py
│   │   │   ├── category_schemas.py
│   │   │   ├── comment_schemas.py
│   │   │   ├── profile_schemas.py
│   │   │   ├── featured_video_schemas.py
│   │   │   ├── subscription_plan_schemas.py
│   │   │   ├── monetization_schemas.py
│   │   │   └── super_admin_monetization_schemas.py
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
│   ├── services/                 # Business Logic & Cloud Orchestration
│   │   ├── admin/                # Creator Admin Services
│   │   │   ├── auth_service.py
│   │   │   ├── tenant_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── video_service.py
│   │   │   ├── playlist_service.py
│   │   │   ├── comment_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── featured_video_service.py
│   │   │   ├── subscription_plan_service.py
│   │   │   ├── monetization_service.py
│   │   │   └── super_admin_monetization_service.py
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
│   │       ├── category_service.py
│   │       └── email_service.py      # Transactional SMTP email delivery engine (HTML & Plain Text)
│   └── utils/                    # Cloud Helper Utilities & Cryptography
│       ├── auth.py               # PBKDF2 password hashing & JWT token encoding/decoding
│       ├── seeder.py             # Idempotent startup seeder for Platform Super Admin & default tenant
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
- **`razorpay-subscription-billing`**: Architectural standards for Razorpay order generation, HMAC-SHA256 payment signature verification, webhook ingestion, subscription plan curation, entitlement state machines, and automated subscription expiration background loops.
- **`ad-monetization-and-settlements`**: Technical standards for Creator Ad Monetization, in-stream Google IMA VAST telemetry beacons, 10-second rapid-fire debouncing, dynamic eCPM resolution, 30% white-label platform commission deduction, bank payout profiles, and Web Admin monthly revenue reconciliation.
- **`creator-studio-analytics-and-curation`**: Guidelines and architectural rules for Creator Admin Studio operations, including honest date-window analytics querying `VideoViewEvent`, automated video publishing workers, featured video curation, comment moderation, category reordering, and branding customization.

---

## Technical Features

- **Multi-Tenant Architecture & Platform Super Admin Controls**: Enterprise-grade multi-tenancy separating platform governance from tenant studio operations. Features a unified `Tenant` entity (merging organization identity and branding attributes), multi-tenant `Admin` accounts bound to `tenant_id`, role-based access control (`super_admin` vs `admin`), and tenant owner designations (`is_owner`). Platform Super Admins can provision new tenants (`POST /api/v1/admin/tenants`), list all tenants (`GET /api/v1/admin/tenants`), activate/deactivate studios, and dynamically switch tenant operational context using the `X-Tenant-Id` header (defaulting to the first active tenant when omitted).
- **Creator Admin Authentication & Dual-Token Session Architecture**: Secure admin identity lifecycle (`/api/v1/admin/auth/*`) enforcing in-memory 30-minute access tokens and 60-day `HttpOnly; Secure; SameSite=Strict` refresh cookies. Features NIST SP 800-132 PBKDF2-HMAC-SHA256 password hashing (600,000 iterations), single-use refresh token rotation, non-destructive multi-device session isolation (ensuring a stale device attempting refresh never disrupts an active session on a newer device), and session profile rehydration (`GET /me`).
- **Atomic Tenant & Creator Studio Onboarding (100% GUI-Driven)**: Zero public registration architecture (`/register` eliminated for anti-abuse). Platform Super Admins atomically provision new tenants and studio owner administrators through the Web Admin Dashboard (`POST /api/v1/admin/tenants`). Each tenant onboarding provisions the `Tenant` entity, the primary owner `Admin` account, and two mandatory subscription tiers (`with_ads` and `no_ads`) within a single ACID database transaction. Idempotent platform startup seeder (`app.utils.seeder`) auto-seeds the Platform Super Admin and default tenant from `.env`.
- **Tenant Staff Administrator Management**: Tenant owners can invite, view, activate/deactivate, and delete staff administrators (`/api/v1/admin/users/*`) bound strictly to their tenant studio, with built-in safety rules preventing the deletion or deactivation of the primary owner.
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
- **Native Email & In-App OTP Authentication, Smart Linking & SMTP Email Delivery**: Native email and password registration and login (`/api/v1/mobile/auth/*`) paired with a self-pruning 6-digit In-App OTP engine (`10-minute expiry`, `5-attempt brute-force lockout`, and `60-second resend cooldown`). Features **Smart Account Linking** to link passwords to existing Google accounts without duplicate profiles or loss of paid subscriptions, and a 2-step In-App Forgot Password flow returning a 10-minute stateless signed JWT reset token. Delivers branded multipart HTML + Plain Text transactional emails via standard SMTP (`smtplib`), supporting Gmail SSL (port 465), AWS SES, Brevo, and standard mail servers, with automatic fallback to local console logging in Developer Mode.
- **Mobile Profile Management & In-Session Admin Password Change**: Self-service subscriber profile endpoints allowing users to update their display name (`PATCH /api/v1/mobile/auth/profile`) and upload custom profile pictures (`POST /api/v1/mobile/auth/profile/photo`) to Bunny Cloud Storage (`assets/avatars/subscribers/subscriber_{user_id}_{timestamp}`) with CDN cache-busting and automatic old asset purge. Includes a unified in-session password change endpoint (`POST /api/v1/admin/auth/change-password`) for **both Tenant Admins and Platform Super Admins** requiring current password re-verification, enforcing 8-character minimum entropy, and rotating `HttpOnly` session cookies.
- **Creator Ad Monetization, Settlements Engine & Dynamic eCPM Architecture**: Comprehensive advertising telemetry and monthly revenue settlement engine. Dispatches Google IMA VAST beacons (`POST /api/v1/mobile/videos/{id}/ad-impression`) with configurable rapid-fire anti-spam debouncing and rolling session caps. Implements a 30% white-label platform technology commission deducted strictly at the eCPM layer ($\text{Creator eCPM} = \text{Raw eCPM} \times 0.70$) without exposing internal margins on creator APIs. Features dynamic historical eCPM baselines (zero hardcoded rates), ₹500 minimum payout threshold rollovers, bank payout profiles with masked account numbers and auto-resolved IFSC codes, and an intuitive GUI-driven monthly revenue settlement and disbursement workflow in the Web Admin Portal.
- **Standardized Pagination Envelopes**: Wraps list queries inside a generic `PaginatedResponse[T]` structure (`total`, `page`, `limit`, `total_pages`, `items`).
- **Insecure Direct Object Reference (IDOR) Protection**: User identity is strictly derived from validated JWT Bearer tokens.

---

## API Summary Breakdown (119 Total Endpoints)

- **Admin Endpoints (72)**:
  - Creator Authentication & Session Lifecycle: 5 endpoints
  - Platform Super Admin Tenant Management: 5 endpoints
  - Tenant Staff Administrator Management: 4 endpoints
  - Studio Dashboard & Analytics: 4 endpoints
  - Video Management & Scheduling: 11 endpoints
  - Playlist Management: 11 endpoints
  - Category Management & Reordering: 5 endpoints
  - Comment Moderation: 6 endpoints
  - Studio Branding & Customization: 4 endpoints
  - Account Profile & Social Links: 3 endpoints
  - Featured Videos Curation: 3 endpoints
  - Subscription Plans Management: 2 endpoints
  - Creator Ad Monetization, Analytics, Payout Settings & Statements: 5 endpoints
  - Platform Super Admin Ad Revenue Reconciliation & Monthly Settlements: 4 endpoints
- **Mobile Endpoints (45)**:
  - Video Catalog, Shorts Swipe Feed, Player, History, Likes, Saves & Ad Telemetry: 14 endpoints
  - Comments & Replies: 6 endpoints
  - Authentication, Registration, Forgot Password, Guest & Profiles: 14 endpoints
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
DATABASE_URL=sqlite:///ott_platform.db

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

## 🚀 Tenant & Creator Studio Onboarding (Platform Super Admin GUI)

The platform operates as an enterprise-grade multi-tenant **White-Labeled Creator OTT Platform**. To eliminate bot account creation, orphaned tenant database records, and credential stuffing attacks, there is intentionally **zero public sign-up (`/register`)** on the Creator Admin portal.

The entire platform is **100% GUI-driven**. Platform Super Admins provision verified tenant studios and their primary owner administrator directly through the **Platform Admin Web Dashboard** (`/admin/tenants`) or via the secure REST API (`POST /api/v1/admin/tenants`):

```http
POST /api/v1/admin/tenants HTTP/1.1
Host: api.talentsea.com
Authorization: Bearer <super_admin_access_token>
Content-Type: application/json

{
  "name": "Acme Media Network",
  "email": "owner@acmestudios.com",
  "password": "SecurePassword123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "tagline": "Premium Cinema & Indie Films",
  "description": "Exclusive cinematic productions and original web series."
}
```

### Onboarding Fields Reference

| Field         |  Type  | Required | Description                                                                             |
| :------------ | :----: | :------: | :-------------------------------------------------------------------------------------- |
| `name`        | String | **Yes**  | Studio / organization name (auto-generates unique URL slug, e.g. `acme-media-network`). |
| `email`       | String | **Yes**  | Owner's login email address (case-insensitive, trimmed, unique).                        |
| `password`    | String | **Yes**  | Initial owner login password (minimum 8 characters, hashed with PBKDF2).                |
| `first_name`  | String |    No    | Owner's first name.                                                                     |
| `last_name`   | String |    No    | Owner's last name.                                                                      |
| `tagline`     | String |    No    | Short branding catchphrase displayed on mobile apps.                                    |
| `description` | String |    No    | Channel/studio biography displayed on mobile app about page.                            |

### 🔒 Atomic Provisioning Invariants

Every tenant creation runs inside a single ACID database transaction (`with db_proxy.atomic():`):

1. **`Tenant` Record**: Merges organization identity and branding attributes (`name`, `slug`, `tagline`, `description`, `is_active=True`).
2. **Owner `Admin` Account**: Created with `role="admin"`, `is_owner=True`, `tenant_id=tenant.id`, and NIST SP 800-132 PBKDF2-HMAC-SHA256 password hashing (600,000 iterations).
3. **Two Fixed Subscription Tiers (`SubscriptionPlan`)**: Automatically seeded with `tenant_id=tenant.id`:
   - **Plan 1 (`Standard with Ads`)**: ₹99/month (`plan_type="with_ads"`, `display_order=1`, `features=["Full video catalog access", "Standard definition (720p) streaming", "Occasional short advertisements", "1 concurrent device stream"]`).
   - **Plan 2 (`Premium Ad-Free`)**: ₹199/month (`plan_type="no_ads"`, `display_order=2`, `features=["100% Ad-free streaming", "Full HD (1080p) resolution", "Offline mobile video downloads", "Up to 3 concurrent device screens", "Early access to new releases"]`).

---

## 💰 Ad Revenue Monthly Settlement & Payouts Workflow (Web GUI & REST APIs)

Platform administrators execute monthly advertising revenue settlements and bank wire disbursements directly through the **Platform Admin Web Dashboard** and REST APIs:

### 1. Monthly Settlement Reconciliation (2-Step Draft & Publish Workflow)

Platform Super Admins review gross revenue reported by Google Ad Manager / programmatic exchanges and execute the monthly reconciliation directly in the GUI (`/admin/monetization/reconciliation`):

- **Draft Phase (`POST /api/v1/admin/monetization/reconciliations`)**: Super Admin inputs gross revenue (`month`, `gross_revenue`, optional `notes`). The system calculates the platform technology commission (30%), net creator pool (70%), gross eCPM, and creator net eCPM, returning a per-tenant projection preview without generating database statements.
- **Publish Phase (`POST /api/v1/admin/monetization/reconciliations/{month}/publish`)**: Locks the draft, transitions status to `"reconciled"` with timestamp `reconciled_at`, and atomically creates all `AdMonthlySettlement` statements for active tenants. Statements receive deterministic IDs (`STMT-{YYYYMM}-TEN{tenant_id}-{hash}`).
- **Threshold Rollovers**: Accounts earning under the minimum threshold (₹500) remain in `"accruing"` and automatically roll forward into the subsequent billing cycle.
- **Bank Details Verification**: Accounts earning $\ge \text{₹500}$ without registered bank details enter `"pending_bank_details"` until bank info is registered in the studio settings.

### 2. Confirm Bank Wire Transfers (Mark Paid with Bank UTR)

On payout day (28th of next month), platform administrators disburse wire transfers (NEFT/RTGS/IMPS) and confirm payments by submitting the official bank UTR code directly via the Web Dashboard or API (`POST /api/v1/admin/monetization/settlements/{statement_id}/mark-paid`):

- Transitions the settlement status from `"reconciled"` to `"paid"`.
- Records the disbursement timestamp (`settled_at`) and official bank UTR reference (`transaction_reference`).
- Optionally attaches a downloadable PDF tax receipt link (`invoice_url`).
- Immediately updates the creator's studio revenue dashboard and statement history.

> **Deterministic Tenant Statement Attribution (`1 Transaction ➔ 1 Tenant`):**  
> Every statement ID follows the deterministic pattern: `STMT-{YYYYMM}-TEN{tenant_id}-{hash}` (e.g. `TEN42` = Tenant Studio ID `42`). In the database, each statement record is uniquely bound to one specific tenant studio via `tenant_id`. Marking a statement as paid directly attributes the bank UTR to that exact tenant's settlement statement.

### 3. Master Platform Financial Ledger & Audits

Platform administrators inspect company-wide monthly revenue, platform profit retained, total creator pool distributed, and historic settlement statements via the Admin GUI and audit ledger API (`GET /api/v1/admin/monetization/reconciliations?page=1&limit=12`).

---

## 🛡️ Tenant Studio Status & Staff Admin Management (Platform Super Admin GUI)

The Web Admin Dashboard provides comprehensive GUI controls for platform governance and tenant staff management:

### 1. Platform Super Admin: Tenant Lifecycle Governance

Super Admins manage tenant studios via the `/admin/tenants` dashboard:

- **List All Tenants**: `GET /api/v1/admin/tenants` (returns tenants, owner email, creation date, and active status).
- **Inspect Tenant Details**: `GET /api/v1/admin/tenants/{id}` (full metadata, branding, and owner profile).
- **Update Tenant Branding**: `PUT /api/v1/admin/tenants/{id}` (updates name, tagline, description).
- **Suspend / Reactivate Tenant Studio**: `PATCH /api/v1/admin/tenants/{id}/status`
  ```json
  {
    "is_active": false,
    "reason": "Terms of service violation"
  }
  ```
  > **Immediate Revocation**: Deactivating a tenant studio immediately invalidates all active JWT refresh sessions for all administrators and subscribers belonging to that tenant, hides public catalog feeds, and disables ad monetization telemetry.

### 2. Tenant Owner: Studio Staff Administrator Management

Tenant owners manage their internal team via the `/admin/users` dashboard:

- **List Staff Administrators**: `GET /api/v1/admin/users` (scoped strictly to the authenticated tenant studio).
- **Invite New Staff Admin**: `POST /api/v1/admin/users`
  ```json
  {
    "email": "editor@acmestudios.com",
    "password": "TemporaryPassword123!",
    "first_name": "Alex",
    "last_name": "Smith"
  }
  ```
- **Toggle Staff Status**: `PATCH /api/v1/admin/users/{id}/status` (`{"is_active": false}`)
- **Delete Staff Member**: `DELETE /api/v1/admin/users/{id}`
  > **Owner Protection**: Built-in safety guards strictly prevent deactivating or deleting the primary tenant owner (`is_owner=True`).

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

# 4. Launch development server with hot-reload:
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Automatic Startup Seeding**:  
> On server startup, the FastAPI lifespan automatically and idempotently executes `app.utils.seeder`:
>
> 1. Provisions the Platform Super Admin from `.env` credentials (`SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD`).
> 2. Provisions the initial default tenant and owner account if the database is newly initialized.
>    No manual CLI execution or provisioning commands required! Log in immediately at `POST /api/v1/admin/auth/login`.

---

## Documentation and Standards

Technical specifications and architecture documentation:

### 🏛️ Database Architecture

- [Complete 24-Table Database Schema Specification](docs/database_architecture_specification.md)

### 💻 Admin Web Portal API Specifications

- [Creator Admin Authentication & Identity Lifecycle API Specification](docs/admin/admin_authentication_api_specification.md)
- [Platform Super Admin Tenant & Staff User Management API Specification](docs/admin/tenant_and_user_management_api_specification.md)
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
- [Platform Super Admin Ad Revenue Reconciliation & Monthly Settlements API Specification](docs/admin/ad_revenue_reconciliation_and_settlement_api_specification.md)

### 📱 Mobile Application API Specifications

- [Mobile Authentication, Email OTP & Profile Specification](docs/mobile/social_authentication_api_specification.md)
- [Mobile Branding Specification](docs/mobile/branding_api_specification.md)
- [Mobile Video Streaming Specification](docs/mobile/video_streaming_api_specification.md)
- [Mobile Categories Specification](docs/mobile/categories_api_specification.md)
- [Mobile Playlists Specification](docs/mobile/playlists_api_specification.md)
- [Mobile Comments Specification](docs/mobile/comments_api_specification.md)
- [Mobile Featured Videos Specification](docs/mobile/featured_videos_api_specification.md)
- [Mobile Subscription Plans Specification](docs/mobile/subscription_plans_api_specification.md)
- [Mobile Payment & Subscriptions Specification](docs/mobile/payment_subscriptions_api_specification.md)
