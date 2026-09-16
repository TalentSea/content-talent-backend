from datetime import datetime, timezone

from peewee import CharField, DateTimeField, PeeweeException, TextField

from app.models.base import BaseModel


class Admin(BaseModel):
    """
    Stores identity, authentication state, creator profile attributes, and social media handles for Web Admin Panel users.
    """

    email = CharField(unique=True, max_length=255, index=True)
    password_hash = CharField(max_length=255, null=True)
    first_name = CharField(max_length=100, null=False)
    last_name = CharField(max_length=100, null=False)
    phone = CharField(max_length=50, null=True)
    location = CharField(max_length=255, null=True)
    bio = TextField(null=True)
    website = CharField(max_length=255, null=True)
    avatar_url = CharField(max_length=500, null=True)
    twitter_url = CharField(max_length=255, null=True)
    youtube_url = CharField(max_length=255, null=True)
    instagram_url = CharField(max_length=255, null=True)
    refresh_token = TextField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    @property
    def name(self) -> str:
        """
        Returns full creator name (first_name + last_name).
        """
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def display_name(self) -> str:
        """
        Returns official studio branding name if set, otherwise creator name.
        """
        try:
            from app.models.branding import Branding

            branding = Branding.get_or_none(Branding.user == self.id)
            if branding and branding.studio_name and branding.studio_name.strip():
                return branding.studio_name.strip()
        except (PeeweeException, AttributeError, ImportError):
            pass
        return self.name

    @property
    def display_avatar_url(self) -> str | None:
        """
        Returns official studio branding logo URL if set, otherwise creator avatar_url.
        """
        try:
            from app.models.branding import Branding

            branding = Branding.get_or_none(Branding.user == self.id)
            if branding and branding.logo_url and branding.logo_url.strip():
                return branding.logo_url.strip()
        except (PeeweeException, AttributeError, ImportError):
            pass
        return self.avatar_url

    class Meta:
        table_name = "admins"
