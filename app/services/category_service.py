from typing import List, Dict, Any
from app.repositories.category_repository import CategoryRepository
from app.schemas.category_schemas import CategoryCreate, CategoryUpdate
from app.database import db_proxy

class CategoryService:
    def __init__(self):
        self.repository = CategoryRepository()

    def get_all_categories(self) -> List[Dict[str, Any]]:
        categories = self.repository.get_all()
        result = []
        for cat in categories:
            cat_dict = cat.__data__
            cat_dict['contentCount'] = self.repository.get_content_count(cat.name)
            cat_dict['createdAt'] = cat.created_at
            result.append(cat_dict)
        return result

    def get_category_by_id(self, category_id: str) -> Dict[str, Any]:
        cat = self.repository.get_by_id(category_id)
        if not cat:
            return None
        cat_dict = cat.__data__
        cat_dict['contentCount'] = self.repository.get_content_count(cat.name)
        cat_dict['createdAt'] = cat.created_at
        return cat_dict

    def create_category(self, data: CategoryCreate) -> Dict[str, Any]:
        cat = self.repository.create(data.model_dump())
        cat_dict = cat.__data__
        cat_dict['createdAt'] = cat.created_at
        return cat_dict

    def update_category(self, category_id: str, data: CategoryUpdate) -> Dict[str, Any]:
        cat = self.repository.update(category_id, data.model_dump(exclude_unset=True))
        if not cat:
            return None
        cat_dict = cat.__data__
        cat_dict['updatedAt'] = cat.created_at
        return cat_dict

    def delete_category(self, category_id: str) -> bool:
        return self.repository.delete(category_id)

    def reorder_categories(self, category_ids: List[str]) -> bool:
        try:
            # Wrap in an atomic database transaction
            with db_proxy.atomic():
                for index, cat_id in enumerate(category_ids):
                    cat = self.repository.get_by_id(cat_id)
                    if cat:
                        cat.order = index + 1
                        cat.save()
            return True
        except Exception:
            return False
