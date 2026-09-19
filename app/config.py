from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings loaded automatically from environment variables (.env).
    """

    DATABASE_URL: str

    BUNNY_STREAM_API_KEY: str
    BUNNY_STREAM_LIBRARY_ID: str = "757205"
    BUNNY_STREAM_TOKEN_KEY: str
    BUNNY_STORAGE_PASSWORD: str
    BUNNY_STORAGE_ZONE_NAME: str = "content-talant-storage"
    BUNNY_PULL_ZONE_URL: str = "https://vz-1294f9c9-1b4.b-cdn.net"
    BUNNY_STORAGE_PULL_ZONE_URL: str = "https://ctcdnin.b-cdn.net"

    JWT_SECRET_KEY: str = "jwt_secret_key"
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60

    BUNNY_TUS_UPLOAD_SIGNATURE_EXPIRE_SECONDS: int = 86400
    BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS: int = 7200
    BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS: int = 7200
    AUTO_PUBLISHER_LOOP_INTERVAL_SECONDS: int = 60
    STALE_GUEST_CLEANUP_DAYS: int = 90
    SUBSCRIPTION_EXPIRATION_LOOP_INTERVAL_SECONDS: int = 3600
    MAX_FEATURED_VIDEOS_PER_CREATOR: int = 10

    GOOGLE_CLIENT_ID: str = (
        "166951692335-a6bblebovsn6ftnrs15n9n8bjpo79o5g.apps.googleusercontent.com"
    )
    FACEBOOK_APP_ID: str = "3169763853213963"
    FACEBOOK_APP_SECRET: str = "bd826b0a4867d0c7033c8f40cc5737dc"

    # Razorpay Payment Gateway Configuration
    RAZORPAY_KEY_ID: str = "rzp_test_TZdrjdhyuxCuaR"
    RAZORPAY_KEY_SECRET: str = "PCl2K30lC250OuKh7R2pxtVA"
    RAZORPAY_WEBHOOK_SECRET: str = "talentsea_webhook_secret_2026"

    # Image Upload Configuration
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,webp,svg"
    MAX_AVATAR_SIZE_MB: int = 2
    MAX_THUMBNAIL_SIZE_MB: int = 5
    MAX_PLAYLIST_COVER_SIZE_MB: int = 5
    MAX_LOGO_SIZE_MB: int = 5
    MAX_BANNER_SIZE_MB: int = 10

    # Video Playback, Anti-Spam Telemetry & Decision Configuration
    VIDEO_VIEW_WATCH_THRESHOLD_PERCENT: float = 30.0
    VIDEO_VIEW_COOLDOWN_MINUTES: int = 30
    VIDEO_VIEW_MAX_DAILY_PER_USER: int = 3
    VIDEO_VIEW_DAILY_WINDOW_HOURS: int = 24
    VIDEO_COMPLETION_THRESHOLD_PERCENT: float = 95.0
    CONTINUE_WATCHING_MIN_SECONDS: int = 10
    POPULARITY_SCORE_LIKE_WEIGHT: int = 3

    # Video Ad Monetization (Google IMA / VAST & Settlements)
    GOOGLE_IMA_VAST_TAG_URL: str = "https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_preroll_skippable&sz=640x480&ciu_szs=300x250%2C728x90&gdfp_req=1&output=vast&unviewed_position_start=1&env=vp&impl=s&correlator="
    PLATFORM_AD_COMMISSION_PERCENT: float = 30.0
    PAYOUT_DAY_OF_MONTH: int = 28
    MIN_PAYOUT_THRESHOLD: float = 500.0
    AD_IMPRESSION_DEBOUNCE_SECONDS: int = 10
    AD_IMPRESSION_SESSION_WINDOW_MINUTES: int = 30
    AD_IMPRESSION_MAX_PER_SESSION: int = 10

    # Platform & Content Defaults
    APP_TIMEZONE: str = "Asia/Kolkata"
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_CATEGORY_COLOR: str = "#3b82f6"

    @property
    def allowed_image_extensions_tuple(self) -> tuple[str, ...]:
        """
        Returns parsed tuple of lowercase allowed image extensions from .env.
        """
        return tuple(
            ext.strip().lower()
            for ext in self.ALLOWED_IMAGE_EXTENSIONS.split(",")
            if ext.strip()
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings configuration object.
    """
    return Settings()
