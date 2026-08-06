import logging
from datetime import datetime, timedelta
from typing import Optional
from peewee import PeeweeException
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.utils.auth import hash_refresh_token, create_refresh_token_string

logger = logging.getLogger(__name__)

class AuthRepository:
    """
    Data access repository for Social Authentication and Refresh Token management.
    """

    def find_user_by_provider_or_email(
        self,
        provider: str,
        provider_id: str,
        email: Optional[str] = None
    ) -> Optional[User]:
        """
        Finds existing user by (provider, provider_id) pair or matching email address.
        """
        try:
            user = User.select().where(
                (User.provider == provider) & (User.provider_id == provider_id)
            ).first()
            if user:
                return user

            if email:
                user_by_email = User.select().where(User.email == email).first()
                if user_by_email:
                    # Associate provider and provider_id if missing
                    user_by_email.provider = provider
                    user_by_email.provider_id = provider_id
                    user_by_email.save()
                    return user_by_email
            return None
        except PeeweeException as e:
            logger.error(f"Error querying user by provider/email: {str(e)}")
            return None

    def create_social_user(
        self,
        provider: str,
        provider_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        role: str = "subscriber"
    ) -> User:
        """
        Creates a new social subscriber user in the database.
        """
        first_name = None
        last_name = None
        if name:
            parts = name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else None

        username_str = email.split("@")[0] if email else f"{provider}_user_{provider_id[:8]}"

        user = User.create(
            username=username_str,
            email=email,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            provider=provider,
            provider_id=provider_id,
            role=role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return user

    def update_user_profile_info(self, user: User, name: Optional[str], avatar_url: Optional[str]) -> User:
        """
        Updates profile avatar or name if updated on social provider.
        """
        updated = False
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if name and not user.first_name:
            parts = name.strip().split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else None
            updated = True

        if updated:
            user.updated_at = datetime.utcnow()
            user.save()
        return user

    def create_refresh_token_record(
        self,
        user: User,
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
            user=user,
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

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user Peewee ORM instance by ID.
        """
        try:
            return User.get_by_id(user_id)
        except Exception:
            return None
