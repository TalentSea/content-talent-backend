from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings loaded automatically from environment variables (.env).
    """

    SQLITE_DB_PATH: str = "ott_platform.db"

    BUNNY_STREAM_API_KEY: str
    BUNNY_STREAM_LIBRARY_ID: str
    BUNNY_STREAM_TOKEN_KEY: str
    BUNNY_STORAGE_PASSWORD: str
    BUNNY_STORAGE_ZONE_NAME: str
    BUNNY_PULL_ZONE_URL: str
    BUNNY_STORAGE_PULL_ZONE_URL: str = "https://talentsea77999.b-cdn.net"

    JWT_SECRET_KEY: str = "talentsea_jwt_secret_key_2026"
    JWT_ALGORITHM: str = "HS256"
    STATIC_API_KEY: str = "talentsea_secret_api_key_2026"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60

    BUNNY_TUS_UPLOAD_SIGNATURE_EXPIRE_SECONDS: int = 86400
    BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS: int = 7200
    BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS: int = 7200
    AUTO_PUBLISHER_LOOP_INTERVAL_SECONDS: int = 60
    STALE_GUEST_CLEANUP_DAYS: int = 90

    GOOGLE_CLIENT_ID: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings configuration object.
    """
    return Settings()
