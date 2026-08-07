import logging
from datetime import datetime, timedelta
from typing import Optional
from peewee import PeeweeException
from app.models.subscriber import Subscriber
from app.models.refresh_token import RefreshToken
from app.utils.auth import hash_refresh_token, create_refresh_token_string

logger = logging.getLogger(__name__)

class AuthRepository:
    """
    Data access repository for Mobile Subscriber Social Authentication and Refresh Token management.
    """

    def find_user_by_provider_or_email(
        self,
        provider: str,
        provider_id: str,
        email: Optional[str] = None
    ) -> Optional[Subscriber]:
        """
        Finds existing subscriber by (provider, provider_id) pair or matching email address.
        """
        try:
            sub = Subscriber.select().where(
                (Subscriber.provider == provider) & (Subscriber.provider_id == provider_id)
            ).first()
            if sub:
                return sub

            if email:
                sub_by_email = Subscriber.select().where(Subscriber.email == email).first()
                if sub_by_email:
                    sub_by_email.provider = provider
                    sub_by_email.provider_id = provider_id
                    sub_by_email.save()
                    return sub_by_email
            return None
        except PeeweeException as e:
            logger.error(f"Error querying subscriber by provider/email: {str(e)}")
            return None

    def create_social_user(
        self,
        provider: str,
        provider_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        role: str = "subscriber"
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return sub

    def update_user_profile_info(self, subscriber: Subscriber, name: Optional[str], avatar_url: Optional[str]) -> Subscriber:
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
            subscriber.updated_at = datetime.utcnow()
            subscriber.save()
        return subscriber

    def create_refresh_token_record(
        self,
        subscriber: Subscriber,
        device_info: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> str:
        """
        Generates a secure refresh token string, hashes it, and stores it in the DB.
        """
        from app.config import get_settings
        if expires_in_days is None:
            expires_in_days = get_settings().REFRESH_TOKEN_EXPIRE_DAYS
        raw_token = create_refresh_token_string()
        token_hash_str = hash_refresh_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        RefreshToken.create(
            user=subscriber,
            token_hash=token_hash_str,
            device_info=device_info,
            expires_at=expires_at,
            is_revoked=False,
            created_at=datetime.utcnow()
        )
        return raw_token

    def get_valid_refresh_token(self, raw_token: str) -> Optional[RefreshToken]:
        """
        Validates raw refresh token against database records.
        """
        token_hash_str = hash_refresh_token(raw_token)
        token_record = RefreshToken.select().where(
            (RefreshToken.token_hash == token_hash_str) &
            (RefreshToken.is_revoked == False) &
            (RefreshToken.expires_at > datetime.utcnow())
        ).first()
        return token_record

    def revoke_refresh_token(self, raw_token: str) -> bool:
        """
        Revokes a refresh token record upon logout.
        """
        token_hash_str = hash_refresh_token(raw_token)
        query = RefreshToken.update(is_revoked=True).where(RefreshToken.token_hash == token_hash_str)
        affected = query.execute()
        return affected > 0

    def get_user_by_id(self, user_id: int) -> Optional[Subscriber]:
        """
        Retrieves a subscriber Peewee ORM instance by ID.
        """
        try:
            return Subscriber.get_by_id(user_id)
        except Exception:
            return None
