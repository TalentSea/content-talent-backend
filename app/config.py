from pydantic_settings import BaseSettings
from functools import lru_cache

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
    
    JWT_SECRET_KEY: str = "talentsea_jwt_secret_key_2026"
    JWT_ALGORITHM: str = "HS256"
    STATIC_API_KEY: str = "talentsea_secret_api_key_2026"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings configuration object.
    """
    return Settings()
