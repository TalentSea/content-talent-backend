import logging
from datetime import datetime, timezone

from peewee import Case, PeeweeException, fn

from app.database import db_proxy
from app.models.category import Category
from app.models.video import Video
from app.utils.string_utils import slugify

logger = logging.getLogger(__name__)


class CategoryRepository:
    """
    Data access layer for Tenant Category operations (Peewee ORM).
    Uses Approach 1 (Dynamic SQL Aggregation for contentCount).
    """

    def list_public_mobile_categories(
        self, tenant_id: int | None = None
    ) -> list[Category]:
        """
        Retrieves all public categories ordered by display_order ascending for mobile catalog filter chips.
        Optionally filters by tenant_id for tenant isolation.
        """
        try:
            query = Category.select()
            if tenant_id is not None:
                query = query.where(Category.tenant == tenant_id)
            return list(query.order_by(Category.display_order.asc()))
        except PeeweeException as e:
            logger.error("Error querying public mobile categories: %s", e)
            raise

    def list_categories(
        self, tenant_id: int, simple: bool = False
    ) -> list[tuple[Category, int]]:
        """
        Retrieves all categories owned by tenant_id. If simple=True, skips Video SQL count queries.
        Ordered by display_order ascending.
        """
        try:
            categories = list(
                Category.select()
                .where(Category.tenant == tenant_id)
                .order_by(Category.display_order.asc())
            )
            if not categories:
                return []

            if simple:
                return [(cat, 0) for cat in categories]

            video_counts_query = (
                Video.select(
                    fn.LOWER(Video.category).alias("cat_name"),
                    fn.COUNT(Video.id).alias("v_count"),
                )
                .where(
                    (Video.tenant == tenant_id)
                    & (Video.category.is_null(False))
                    & (fn.LOWER(Video.status) == "published")
                    & (Video.is_playable == True)
                )
                .group_by(fn.LOWER(Video.category))
            )
            counts_map = {row.cat_name: row.v_count for row in video_counts_query}
            return [
                (cat, counts_map.get(cat.name.lower().strip(), 0)) for cat in categories
            ]
        except PeeweeException as e:
            logger.error("Error querying categories for tenant %s: %s", tenant_id, e)
            raise

    def get_category_by_id(self, category_id: int, tenant_id: int) -> Category | None:
        """
        Fetches a category by integer primary key ID ensuring tenant ownership authorization.
        """
        try:
            return Category.get_or_none(
                (Category.id == category_id) & (Category.tenant == tenant_id)
            )
        except PeeweeException as e:
            logger.error("Error fetching category %s: %s", category_id, e)
            raise

    def get_category_by_name(self, name: str, tenant_id: int) -> Category | None:
        """
        Fetches a category by name ensuring unique constraints per tenant.
        """
        try:
            return Category.get_or_none(
                (fn.LOWER(Category.name) == name.lower().strip())
                & (Category.tenant == tenant_id)
            )
        except PeeweeException as e:
            logger.error("Error fetching category by name '%s': %s", name, e)
            raise

    def create_category(self, tenant_id: int, data: dict) -> Category:
        """
        Creates a new category record. Auto-generates slug and calculates display_order.
        """
        try:
            name = data.get("name", "").strip()
            slug = slugify(name)

            # Calculate next display_order
            max_order = (
                Category.select(fn.MAX(Category.display_order))
                .where(Category.tenant == tenant_id)
                .scalar()
                or 0
            )
            new_order = max_order + 1

            from app.config import get_settings

            settings = get_settings()
            return Category.create(
                tenant=tenant_id,
                name=name,
                slug=slug,
                description=data.get("description"),
                thumbnail_url=data.get("thumbnail_url"),
                color=data.get("color") or settings.DEFAULT_CATEGORY_COLOR,
                display_order=new_order,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        except PeeweeException as e:
            logger.error("Error creating category for tenant %s: %s", tenant_id, e)
            raise

    def update_category(
        self, category_id: int, tenant_id: int, update_data: dict
    ) -> Category | None:
        """
        Updates fields of an existing category. Updates slug if name changes.
        """
        try:
            with db_proxy.atomic():
                cat = self.get_category_by_id(category_id, tenant_id)
                if not cat:
                    return None

                if update_data.get("name"):
                    old_name = cat.name
                    new_name = update_data["name"].strip()
                    if old_name.lower().strip() != new_name.lower():
                        Video.update(category=new_name).where(
                            (Video.tenant == tenant_id)
                            & (fn.LOWER(Video.category) == old_name.lower().strip())
                        ).execute()
                    cat.name = new_name
                    cat.slug = slugify(new_name)
                if "description" in update_data:
                    cat.description = update_data["description"]
                if "thumbnail_url" in update_data:
                    cat.thumbnail_url = update_data["thumbnail_url"]
                if update_data.get("color"):
                    cat.color = update_data["color"]

                cat.updated_at = datetime.now(timezone.utc)
                cat.save()
                return cat
        except PeeweeException as e:
            logger.error("Error updating category %s: %s", category_id, e)
            raise

    def delete_category(self, category_id: int, tenant_id: int) -> bool:
        """
        Deletes a category and unassigns videos (setting Video.category = None) so assets remain intact.
        """
        try:
            with db_proxy.atomic():
                cat = self.get_category_by_id(category_id, tenant_id)
                if not cat:
                    return False

                # Unlink associated videos safely
                Video.update(category=None).where(
                    (Video.tenant == tenant_id)
                    & (fn.LOWER(Video.category) == cat.name.lower().strip())
                ).execute()

                cat.delete_instance()
                return True
        except PeeweeException as e:
            logger.error("Error deleting category %s: %s", category_id, e)
            raise

    def reorder_categories(self, tenant_id: int, category_ids: list[int]) -> bool:
        """
        Atomically updates category display_order values in 1 single bulk CASE query.
        """
        if not category_ids:
            return True
        try:
            whens = [(cat_id, idx + 1) for idx, cat_id in enumerate(category_ids)]
            order_case = Case(Category.id, whens)
            with db_proxy.atomic():
                Category.update(display_order=order_case).where(
                    (Category.tenant == tenant_id) & (Category.id.in_(category_ids))
                ).execute()
            return True
        except PeeweeException as e:
            logger.error("Error reordering categories for tenant %s: %s", tenant_id, e)
            raise
