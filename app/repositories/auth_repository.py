import logging
from datetime import datetime, timedelta, timezone

from peewee import PeeweeException

from app.config import get_settings
from app.models.refresh_token import RefreshToken
from app.models.subscriber import Subscriber
from app.utils.auth import create_refresh_token_string, hash_refresh_token

logger = logging.getLogger(__name__)


class AuthRepository:
    """
    Data access repository for Mobile Subscriber Social Authentication and Refresh Token management.
    """

    def find_user_by_provider_or_email(
        self, provider: str, provider_id: str, email: str | None = None
    ) -> Subscriber | None:
        """
        Finds existing subscriber by (provider, provider_id) pair or matching email address.
        """
        try:
            sub = (
                Subscriber.select()
                .where(
                    (Subscriber.provider == provider)
                    & (Subscriber.provider_id == provider_id)
                )
                .first()
            )
            if sub:
                return sub

            if email:
                sub_by_email = (
                    Subscriber.select().where(Subscriber.email == email).first()
                )
                if sub_by_email:
                    sub_by_email.provider = provider
                    sub_by_email.provider_id = provider_id
                    sub_by_email.save()
                    return sub_by_email
            return None
        except PeeweeException as e:
            logger.error(f"Error querying subscriber by provider/email: {e!s}")
            return None

    def create_social_user(
        self,
        provider: str,
        provider_id: str,
        email: str | None = None,
        name: str | None = None,
        avatar_url: str | None = None,
        role: str = "subscriber",
    ) -> Subscriber:
        """
        Creates a new social subscriber in the database.
        """
        sub = Subscriber.create(
            email=email,
            name=name,
            avatar_url=avatar_url,
            provider=provider,
            provider_id=provider_id,
            role=role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return sub

    def update_user_profile_info(
        self, subscriber: Subscriber, name: str | None, avatar_url: str | None
    ) -> Subscriber:
        """
        Updates profile avatar or name if updated on social provider.
        """
        updated = False
        if avatar_url and subscriber.avatar_url != avatar_url:
            subscriber.avatar_url = avatar_url
            updated = True
        if name and not subscriber.name:
            subscriber.name = name
            updated = True

        if updated:
            subscriber.updated_at = datetime.now(timezone.utc)
            subscriber.save()
        return subscriber

    def create_refresh_token_record(
        self,
        subscriber: Subscriber,
        device_info: str | None = None,
        expires_in_days: int | None = None,
    ) -> str:
        """
        Generates a secure refresh token string, hashes it, and stores it in the DB.
        """
        if expires_in_days is None:
            expires_in_days = get_settings().REFRESH_TOKEN_EXPIRE_DAYS
        raw_token = create_refresh_token_string()
        token_hash_str = hash_refresh_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        RefreshToken.create(
            user=subscriber,
            token_hash=token_hash_str,
            device_info=device_info,
            expires_at=expires_at,
            is_revoked=False,
            created_at=datetime.now(timezone.utc),
        )
        return raw_token

    def get_valid_refresh_token(self, raw_token: str) -> RefreshToken | None:
        """
        Validates raw refresh token against database records.
        """
        token_hash_str = hash_refresh_token(raw_token)
        token_record = (
            RefreshToken.select()
            .where(
                (RefreshToken.token_hash == token_hash_str)
                & (RefreshToken.is_revoked == False)
                & (RefreshToken.expires_at > datetime.now(timezone.utc))
            )
            .first()
        )
        return token_record

    def revoke_refresh_token(self, raw_token: str) -> bool:
        """
        Revokes a refresh token record upon logout.
        """
        token_hash_str = hash_refresh_token(raw_token)
        query = RefreshToken.update(is_revoked=True).where(
            RefreshToken.token_hash == token_hash_str
        )
        affected = query.execute()
        return affected > 0

    def get_user_by_id(self, user_id: int) -> Subscriber | None:
        """
        Retrieves a subscriber Peewee ORM instance by ID.
        """
        try:
            return Subscriber.get_or_none(Subscriber.id == user_id)
        except PeeweeException:
            return None

    def get_or_create_guest_subscriber(self, device_id: str) -> Subscriber:
        """
        Finds existing guest subscriber by device_id or creates a new anonymous guest subscriber.
        Refreshes updated_at timestamp on active guest sessions.
        """
        now = datetime.now(timezone.utc)
        sub = (
            Subscriber.select()
            .where(
                (Subscriber.provider == "guest") & (Subscriber.provider_id == device_id)
            )
            .first()
        )

        if sub:
            sub.updated_at = now
            sub.save()
            return sub

        sub = Subscriber.create(
            name="Guest User",
            email=None,
            avatar_url=None,
            provider="guest",
            provider_id=device_id,
            role="guest",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        return sub

    def upgrade_guest_subscriber(
        self,
        guest_subscriber_id: int,
        provider: str,
        provider_id: str,
        email: str | None = None,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> Subscriber:
        """
        Upgrades an existing Guest subscriber record in-place to a permanent Google/Facebook subscriber.
        Preserves all Watch History, Watchlist, and Liked Videos attached to subscriber ID!
        """
        sub = self.get_user_by_id(guest_subscriber_id)
        if not sub:
            return self.create_social_user(
                provider=provider,
                provider_id=provider_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
                role="subscriber",
            )

        now = datetime.now(timezone.utc)
        sub.provider = provider
        sub.provider_id = provider_id
        if email:
            sub.email = email
        if name:
            sub.name = name
        if avatar_url:
            sub.avatar_url = avatar_url
        sub.role = "subscriber"
        sub.updated_at = now
        sub.save()
        return sub

    def cleanup_stale_guest_subscribers(self, days: int = 90) -> int:
        """
        Deletes abandoned guest subscriber records with updated_at < NOW() - 90 days.
        Cascades delete to associated watch_history, video_saves, and video_likes.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_count = (
            Subscriber.delete()
            .where(
                (Subscriber.provider == "guest")
                & (Subscriber.role == "guest")
                & (Subscriber.updated_at < cutoff_date)
            )
            .execute()
        )
        logger.info(
            f"Cleaned up {deleted_count} stale guest subscribers older than {days} days."
        )
        return deleted_count
