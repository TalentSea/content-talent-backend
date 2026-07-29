import logging
from typing import Optional, Dict, Any
from datetime import datetime
from peewee import PeeweeException

from app.models.user import User

logger = logging.getLogger(__name__)

class ProfileRepository:
    """
    Data access layer for User Profile operations (Peewee ORM).
    """

    def get_profile_by_user_id(self, user_id: int) -> Optional[User]:
        """
        Fetches the user record by primary key ID.
        """
        try:
            return User.get_or_none(User.id == user_id)
        except PeeweeException as e:
            logger.error(f"Error fetching profile for user {user_id}: {str(e)}")
            raise e

    def update_profile(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Updates profile textual attributes and social links in database (excluding email).
        """
        user = self.get_profile_by_user_id(user_id)
        if not user:
            return None

        social = update_data.get("social_links") or {}
        
        if "first_name" in update_data:
            user.first_name = update_data["first_name"]
        if "last_name" in update_data:
            user.last_name = update_data["last_name"]
        if "phone" in update_data:
            user.phone = update_data["phone"]
        if "location" in update_data:
            user.location = update_data["location"]
        if "bio" in update_data:
            user.bio = update_data["bio"]
        if "website" in update_data:
            user.website = update_data["website"]

        # Social links mapping
        if "twitter" in social:
            user.twitter_url = social["twitter"]
        if "youtube" in social:
            user.youtube_url = social["youtube"]
        if "instagram" in social:
            user.instagram_url = social["instagram"]

        user.updated_at = datetime.now()
        user.save()
        return user

    def update_avatar_url(self, user_id: int, avatar_url: str) -> Optional[User]:
        """
        Persists the newly uploaded avatar CDN URL in DB.
        """
        user = self.get_profile_by_user_id(user_id)
        if not user:
            return None

        user.avatar_url = avatar_url
        user.updated_at = datetime.now()
        user.save()
        return user
