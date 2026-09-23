import json

from peewee import BooleanField, CharField, DateTimeField, TextField

from app.models.base import BaseModel
from app.utils.date_utils import now_utc
from app.utils.string_utils import slugify

DEFAULT_THEME_COLORS: dict[str, str] = {
    "primaryColor": "#E50914",
    "secondaryColor": "#5865F2",
    "activeStateColor": "#5865F2",
    "mainBackgroundColor": "#000000",
    "cardBackgroundColor": "#12121A",
    "primaryTextColor": "#FFFFFF",
    "secondaryTextColor": "#9CA3AF",
    "mutedTextColor": "#6B7280",
    "buttonTextColor": "#FFFFFF",
}


class Tenant(BaseModel):
    """
    Unified multi-tenancy and brand entity representing a White-Label Studio / Tenant.
    Stores brand identity, visual assets, theme palette, and platform operational state.
    """

    name = CharField(max_length=255, unique=True, index=True)
    slug = CharField(max_length=255, unique=True, index=True)
    tagline = CharField(max_length=255, null=True)
    description = TextField(null=True)
    logo_url = CharField(max_length=500, null=True)
    banner_url = CharField(max_length=500, null=True)
    twitter_url = CharField(max_length=255, null=True)
    youtube_url = CharField(max_length=255, null=True)
    instagram_url = CharField(max_length=255, null=True)
    theme_colors = TextField(null=True)
    is_active = BooleanField(default=True, index=True)
    deactivation_reason = TextField(null=True)
    deactivated_at = DateTimeField(null=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    def get_theme_colors(self) -> dict[str, str]:
        """
        Returns the tenant's theme colors as a dictionary.
        Safely deserializes stored JSON and merges with default tokens
        so all 9 color properties are guaranteed non-null.
        """
        palette = dict(DEFAULT_THEME_COLORS)
        if self.theme_colors:
            try:
                stored = json.loads(self.theme_colors)
                if isinstance(stored, dict):
                    for k, v in stored.items():
                        if v:
                            palette[k] = v
            except Exception:  # noqa: BLE001, S110
                pass
        return palette

    def set_theme_colors(self, colors: dict[str, str]) -> None:
        """
        Updates theme colors dictionary and persists it as a JSON string.
        """
        current = self.get_theme_colors()
        for k, v in colors.items():
            if v is not None:
                current[k] = str(v).strip()
        self.theme_colors = json.dumps(current)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        if not self.theme_colors:
            self.theme_colors = json.dumps(DEFAULT_THEME_COLORS)
        return super().save(*args, **kwargs)

    class Meta:
        table_name = "tenants"
