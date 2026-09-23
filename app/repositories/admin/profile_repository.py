import logging
from datetime import datetime, timezone
from typing import Any

import peewee
from peewee import PeeweeException

from app.models.admin import Admin
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


class ProfileRepository:
    """
    Data access layer for Admin Creator Profile operations (Peewee ORM).
    """

    def get_profile_by_admin_id(self, admin_id: int) -> Admin | None:
        """
        Fetches the admin creator record by primary key ID.
        """
        try:
            return Admin.select(Admin, Tenant).join(Tenant, peewee.JOIN.LEFT_OUTER).where(Admin.id == admin_id).first()
        except PeeweeException as e:
            logger.error("Error fetching profile for admin %s: %s", admin_id, e)
            raise

    def update_profile(
        self, admin_id: int, update_data: dict[str, Any]
    ) -> Admin | None:
        """
        Updates profile textual attributes and social links in database (excluding email).
        """
        admin = self.get_profile_by_admin_id(admin_id)
        if not admin:
            return None

        social = update_data.get("social_links") or {}

        if "first_name" in update_data:
            admin.first_name = update_data["first_name"]
        if "last_name" in update_data:
            admin.last_name = update_data["last_name"]
        if "phone" in update_data:
            admin.phone = update_data["phone"]
        if "location" in update_data:
            admin.location = update_data["location"]
        if "bio" in update_data:
            admin.bio = update_data["bio"]
        if "website" in update_data:
            admin.website = update_data["website"]

        # Social links mapping to Tenant (strictly guarded: only tenant primary owner can modify studio branding links)
        if admin.tenant and social and admin.is_owner:
            if "twitter" in social:
                admin.tenant.twitter_url = social["twitter"]
            if "youtube" in social:
                admin.tenant.youtube_url = social["youtube"]
            if "instagram" in social:
                admin.tenant.instagram_url = social["instagram"]
            admin.tenant.updated_at = datetime.now(timezone.utc)
            admin.tenant.save()

        admin.updated_at = datetime.now(timezone.utc)
        admin.save()
        return admin

    def update_avatar_url(self, admin_id: int, avatar_url: str) -> Admin | None:
        """
        Persists the newly uploaded avatar CDN URL in DB.
        """
        admin = self.get_profile_by_admin_id(admin_id)
        if not admin:
            return None

        admin.avatar_url = avatar_url
        admin.updated_at = datetime.now(timezone.utc)
        admin.save()
        return admin
