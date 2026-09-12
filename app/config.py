from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings loaded automatically from environment variables (.env).
    """

    SQLITE_DB_PATH: str

    BUNNY_STREAM_API_KEY: str
    BUNNY_STREAM_LIBRARY_ID: str
    BUNNY_STREAM_TOKEN_KEY: str
    BUNNY_STORAGE_PASSWORD: str
    BUNNY_STORAGE_ZONE_NAME: str
    BUNNY_PULL_ZONE_URL: str
    BUNNY_STORAGE_PULL_ZONE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    STATIC_API_KEY: str = "talentsea_secret_api_key_2026"

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    BUNNY_TUS_UPLOAD_SIGNATURE_EXPIRE_SECONDS: int
    BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS: int
    BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS: int
    AUTO_PUBLISHER_LOOP_INTERVAL_SECONDS: int
    STALE_GUEST_CLEANUP_DAYS: int
    SUBSCRIPTION_EXPIRATION_LOOP_INTERVAL_SECONDS: int
    MAX_FEATURED_VIDEOS_PER_CREATOR: int

    GOOGLE_CLIENT_ID: str
    FACEBOOK_APP_ID: str
    FACEBOOK_APP_SECRET: str

    # Razorpay Payment Gateway Configuration
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str

    # Image Upload Configuration
    ALLOWED_IMAGE_EXTENSIONS: str
    MAX_AVATAR_SIZE_MB: int
    MAX_THUMBNAIL_SIZE_MB: int
    MAX_PLAYLIST_COVER_SIZE_MB: int
    MAX_LOGO_SIZE_MB: int
    MAX_BANNER_SIZE_MB: int

    # Video Playback, Anti-Spam Telemetry & Decision Configuration
    VIDEO_VIEW_WATCH_THRESHOLD_PERCENT: float
    VIDEO_VIEW_COOLDOWN_MINUTES: int
    VIDEO_VIEW_MAX_DAILY_PER_USER: int
    VIDEO_VIEW_DAILY_WINDOW_HOURS: int
    VIDEO_COMPLETION_THRESHOLD_PERCENT: float
    CONTINUE_WATCHING_MIN_SECONDS: int
    POPULARITY_SCORE_LIKE_WEIGHT: int

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
