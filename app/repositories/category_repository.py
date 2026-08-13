import logging
import re
from typing import Optional, List, Tuple
from datetime import datetime
from peewee import fn, PeeweeException

from app.models.category import Category
from app.models.video import Video

logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """Utility helper converting arbitrary text to clean URL-safe slug string."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

class CategoryRepository:
    """
    Data access layer for Creator Admin Category operations (Peewee ORM).
    Uses Approach 1 (Dynamic SQL Aggregation for contentCount).
    """

    def list_public_mobile_categories(self) -> List[Category]:
        """
        Retrieves all public categories ordered by display_order ascending for mobile catalog filter chips.
        """
        try:
            return list(Category.select().order_by(Category.display_order.asc()))
        except PeeweeException as e:
            logger.error(f"Error querying public mobile categories: {str(e)}")
            raise e

    def list_categories(self, user_id: int, simple: bool = False) -> List[Tuple[Category, int]]:
        """
        Retrieves all categories owned by user_id. If simple=True, skips Video SQL count queries.
        Ordered by display_order ascending.
        """
        try:
            categories = list(Category.select().where(Category.user == user_id).order_by(Category.display_order.asc()))
            if not categories:
                return []

            if simple:
                return [(cat, 0) for cat in categories]

            results = []
            for cat in categories:
                count = Video.select().where(
                    (Video.user == user_id) &
                    (fn.LOWER(Video.category) == cat.slug) &
                    (fn.LOWER(Video.status).in_(["published", "ready"])) &
                    (Video.is_playable == True)
                ).count()
                results.append((cat, count))

            return results
        except PeeweeException as e:
            logger.error(f"Error querying categories for user {user_id}: {str(e)}")
            raise e

    def get_category_by_id(self, category_id: int, user_id: int) -> Optional[Category]:
        """
        Fetches a category by integer primary key ID ensuring user ownership authorization.
        """
        try:
            return Category.get_or_none((Category.id == category_id) & (Category.user == user_id))
        except PeeweeException as e:
            logger.error(f"Error fetching category {category_id}: {str(e)}")
            raise e

    def get_category_by_name(self, name: str, user_id: int) -> Optional[Category]:
        """
        Fetches a category by name ensuring unique constraints per user.
        """
        try:
            return Category.get_or_none((fn.LOWER(Category.name) == name.lower().strip()) & (Category.user == user_id))
        except PeeweeException as e:
            logger.error(f"Error fetching category by name '{name}': {str(e)}")
            raise e

    def create_category(self, user_id: int, data: dict) -> Category:
        """
        Creates a new category record. Auto-generates slug and calculates display_order.
        """
        try:
            name = data.get("name", "").strip()
            slug = slugify(name)
            
            # Calculate next display_order
            max_order = Category.select(fn.MAX(Category.display_order)).where(Category.user == user_id).scalar() or 0
            new_order = max_order + 1

            return Category.create(
                user=user_id,
                name=name,
                slug=slug,
                description=data.get("description"),
                icon=data.get("icon") or "📁",
                color=data.get("color") or "#3b82f6",
                display_order=new_order,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        except PeeweeException as e:
            logger.error(f"Error creating category for user {user_id}: {str(e)}")
            raise e

    def update_category(self, category_id: int, user_id: int, update_data: dict) -> Optional[Category]:
        """
        Updates fields of an existing category. Updates slug if name changes.
        """
        try:
            cat = self.get_category_by_id(category_id, user_id)
            if not cat:
                return None

            if "name" in update_data and update_data["name"]:
                cat.name = update_data["name"].strip()
                cat.slug = slugify(cat.name)
            if "description" in update_data and update_data["description"] is not None:
                cat.description = update_data["description"]
            if "icon" in update_data and update_data["icon"]:
                cat.icon = update_data["icon"]
            if "color" in update_data and update_data["color"]:
                cat.color = update_data["color"]

            cat.updated_at = datetime.now()
            cat.save()
            return cat
        except PeeweeException as e:
            logger.error(f"Error updating category {category_id}: {str(e)}")
            raise e

    def delete_category(self, category_id: int, user_id: int) -> bool:
        """
        Deletes a category and unassigns videos (setting Video.category = None) so assets remain intact.
        """
        try:
            cat = self.get_category_by_id(category_id, user_id)
            if not cat:
                return False

            # Unlink associated videos safely
            Video.update(category=None).where(
                (Video.user == user_id) &
                (fn.LOWER(Video.category) == cat.slug)
            ).execute()

            cat.delete_instance()
            return True
        except PeeweeException as e:
            logger.error(f"Error deleting category {category_id}: {str(e)}")
            raise e

    def reorder_categories(self, user_id: int, category_ids: List[int]) -> bool:
        """
        Atomically updates category display_order values according to array order.
        """
        try:
            for idx, cat_id in enumerate(category_ids):
                Category.update(display_order=idx + 1).where(
                    (Category.id == cat_id) &
                    (Category.user == user_id)
                ).execute()
            return True
        except PeeweeException as e:
            logger.error(f"Error reordering categories for user {user_id}: {str(e)}")
            raise e
