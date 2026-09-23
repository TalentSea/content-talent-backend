from datetime import date, datetime, timezone
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


def get_date_range_for_month(month_str: str) -> tuple[datetime, datetime]:
    """
    Parses a string like 'YYYY-MM' into a start and exclusive end datetime (UTC).
    Useful for querying monthly database records.
    """
    year, month = map(int, month_str.split("-"))
    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start_date, end_date


def get_scheduled_payout_date(month_str: str) -> date:
    """
    Calculates the 28th of the next month given a 'YYYY-MM' string.
    This is the standard scheduled bank payout date for a billing cycle.
    """
    year, m = map(int, month_str.split("-"))
    if m == 12:
        return date(year + 1, 1, 28)
    return date(year, m + 1, 28)
