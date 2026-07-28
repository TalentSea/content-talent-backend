from typing import List, Optional
from peewee import fn
from app.models.category import Category
from app.models.video import Video

class CategoryRepository:
    def get_all(self) -> List[Category]:
        # Always fetch sorted by display order
        return list(Category.select().order_by(Category.order.asc()))

    def get_by_id(self, category_id: str) -> Optional[Category]:
        return Category.get_or_none(Category.id == category_id)

    def create(self, category_data: dict) -> Category:
        # Step 1: Query max order
        max_order_query = Category.select(fn.MAX(Category.order)).scalar()
        max_order = max_order_query if max_order_query is not None else 0
        
        # Step 2: Assign max_order + 1 to keep category at the bottom
        category_data['order'] = max_order + 1
        return Category.create(**category_data)

    def update(self, category_id: str, update_data: dict) -> Optional[Category]:
        category = self.get_by_id(category_id)
        if not category:
            return None
            
        for k, v in update_data.items():
            if v is not None:
                setattr(category, k, v)
        category.save()
        return category

    def delete(self, category_id: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False
        category.delete_instance()
        return True

    def get_content_count(self, category_name: str) -> int:
        # Querying count from Video table matching current category name
        return Video.select().where(Video.category == category_name).count()
