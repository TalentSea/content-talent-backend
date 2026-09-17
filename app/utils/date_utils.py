from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import get_settings


def get_app_timezone() -> ZoneInfo:
    """
    Returns the official operating ZoneInfo timezone configured for this white-label platform instance.
    Reads dynamically from APP_TIMEZONE in .env (defaults to 'Asia/Kolkata').
    """
    settings = get_settings()
    tz_name = getattr(settings, "APP_TIMEZONE", "Asia/Kolkata")
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return ZoneInfo("Asia/Kolkata")


def now_utc() -> datetime:
    """
    Returns the current timezone-aware UTC datetime.
    Standard single source of truth for all database timestamp columns.
    """
    return datetime.now(timezone.utc)


def to_app_timezone(dt: datetime | None = None) -> datetime:
    """
    Converts a UTC or naive datetime into the platform's configured local operating timezone.
    If dt is None, returns the current time in the application timezone.
    """
    tz = get_app_timezone()
    if dt is None:
        return datetime.now(tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(tz)
    return dt.astimezone(tz)
