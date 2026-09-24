import logging
from datetime import datetime, timezone

from peewee import PeeweeException, fn

from app.models.admin import Admin

logger = logging.getLogger(__name__)


class AuthRepository:
    """
    Data access repository for Creator Admin authentication and session tokens (Peewee ORM).
    """

    def get_admin_by_email(self, email: str) -> Admin | None:
        """
        Queries an Admin record by case-insensitive email address.
        """
        try:
            return Admin.get_or_none(fn.LOWER(Admin.email) == email.strip().lower())
        except PeeweeException as e:
            logger.error("Error querying admin by email %s: %s", email, e)
            raise

    def get_admin_by_id(self, admin_id: int) -> Admin | None:
        """
        Queries an Admin record by primary key ID.
        """
        try:
            return Admin.get_or_none(Admin.id == admin_id)
        except PeeweeException as e:
            logger.error("Error querying admin by id %s: %s", admin_id, e)
            raise

    def get_admin_by_refresh_token_hash(self, token_hash: str) -> Admin | None:
        """
        Queries an Admin record matching the stored SHA-256 refresh token hash.
        """
        try:
            return Admin.get_or_none(Admin.refresh_token == token_hash)
        except PeeweeException as e:
            logger.error("Error querying admin by refresh token hash: %s", e)
            raise

    def update_refresh_token_hash(
        self, admin_id: int, token_hash: str | None
    ) -> bool:
        """
        Updates the stored refresh token hash for an admin (or clears it on logout).
        """
        try:
            rows_updated = (
                Admin.update(
                    refresh_token=token_hash,
                    updated_at=datetime.now(timezone.utc),
                )
                .where(Admin.id == admin_id)
                .execute()
            )
            return rows_updated > 0
        except PeeweeException as e:
            logger.error(
                "Error updating refresh token hash for admin %s: %s", admin_id, e
            )
            raise

    def update_admin_password(self, admin_id: int, password_hash: str) -> bool:
        """
        Updates the stored password hash for an admin record.
        """
        try:
            rows_updated = (
                Admin.update(
                    password_hash=password_hash,
                    updated_at=datetime.now(timezone.utc),
                )
                .where(Admin.id == admin_id)
                .execute()
            )
            return rows_updated > 0
        except PeeweeException as e:
            logger.error("Error updating password for admin %s: %s", admin_id, e)
            raise

