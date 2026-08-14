import logging

logger = logging.getLogger(__name__)


def parse_duration_seconds(val) -> int:
    """
    Safely parses duration string ('02:58', '01:15:30', or raw integer/numeric seconds) into integer seconds.
    Returns 0 if None, empty, or unparseable.
    """
    if not val:
        return 0
    if isinstance(val, int):
        return val
    try:
        val_str = str(val).strip()
        if val_str.isdigit():
            return int(val_str)
        if ":" in val_str:
            parts = [int(p) for p in val_str.split(":")]
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
        return int(val_str)
    except (ValueError, TypeError, AttributeError):
        return 0


def calculate_completion_percentage(
    last_position_seconds: int | None,
    video_duration: str | int | None,
    history_id: int | None = None,
) -> float:
    """
    Safely calculates watch progress percentage (0.0 to 100.0) from last position and video duration.
    Logs a server warning trace if duration or calculation data is invalid.
    """
    try:
        if not video_duration:
            return 0.0
        dur = parse_duration_seconds(video_duration)
        if dur <= 0:
            return 0.0
        pos = last_position_seconds or 0
        return round(min(100.0, (pos / float(dur)) * 100.0), 1)
    except (AttributeError, ValueError, TypeError, ZeroDivisionError) as err:
        logger.warning(
            f"Failed to compute completion percentage (WatchHistory ID: {history_id or 'N/A'}): {err!s}"
        )
        return 0.0
