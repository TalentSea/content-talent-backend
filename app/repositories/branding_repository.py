from datetime import datetime, timezone
from typing import Any

from app.models.branding import Branding


class BrandingRepository:
    """
    Data access repository for Creator Branding records in the database.
    """

    def get_by_user_id(self, user_id: int) -> Branding | None:
        """
        Retrieves the branding record for a creator by admin user_id.
        """
        return Branding.get_or_none(Branding.user_id == user_id)

    def get_or_create_branding(self, user_id: int) -> Branding:
        """
        Retrieves or initializes a default branding record for an admin creator.
        """
        branding, _ = Branding.get_or_create(user_id=user_id)
        return branding

    def update_branding_text(
        self, user_id: int, fields: dict[str, Any]
    ) -> Branding:
        """
        Applies partial updates to text fields (creator_name, tagline, description) and updates updated_at.
        """
        branding = self.get_or_create_branding(user_id)
        for key, value in fields.items():
            if value is not None and hasattr(branding, key):
                setattr(branding, key, value)
        branding.updated_at = datetime.now(timezone.utc)
        branding.save()
        return branding

    def update_logo_url(self, user_id: int, logo_url: str) -> Branding:
        """
        Updates the logo_url and updated_at timestamp.
        """
        branding = self.get_or_create_branding(user_id)
        branding.logo_url = logo_url
        branding.updated_at = datetime.now(timezone.utc)
        branding.save()
        return branding

    def update_banner_url(self, user_id: int, banner_url: str) -> Branding:
        """
        Updates the banner_url and updated_at timestamp.
        """
        branding = self.get_or_create_branding(user_id)
        branding.banner_url = banner_url
        branding.updated_at = datetime.now(timezone.utc)
        branding.save()
        return branding
