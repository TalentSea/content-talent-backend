import re


def slugify(text: str) -> str:
    """Generates a URL-friendly slug from an arbitrary string."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


def format_full_name(first_name: str | None, last_name: str | None) -> str:
    """Safely formats a full name string accounting for nulls."""
    return f"{first_name or ''} {last_name or ''}".strip()
