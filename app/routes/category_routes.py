from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.schemas.category_schemas import (
    CategoryCreate, 
    CategoryUpdate, 
    CategoryResponse, 
    CategoryListResponse,
    CategoryReorderRequest
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])

def get_category_service():
    return CategoryService()

@router.get("", response_model=CategoryListResponse)
def get_all_categories(service: CategoryService = Depends(get_category_service)):
    categories = service.get_all_categories()
    return {"data": categories}

@router.get("/{id}", response_model=CategoryResponse)
def get_category(id: str, service: CategoryService = Depends(get_category_service)):
    category = service.get_category_by_id(id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("", response_model=Dict[str, Any], status_code=201)
def create_category(category_in: CategoryCreate, service: CategoryService = Depends(get_category_service)):
    new_category = service.create_category(category_in)
    return {
        "id": new_category["id"],
        "name": new_category["name"],
        "createdAt": new_category["createdAt"]
    }

@router.put("/reorder")
def reorder_categories(request: CategoryReorderRequest, service: CategoryService = Depends(get_category_service)):
    success = service.reorder_categories(request.ids)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder categories")
    return {"message": "Category order updated"}

@router.put("/{id}", response_model=Dict[str, Any])
def update_category(id: str, category_in: CategoryUpdate, service: CategoryService = Depends(get_category_service)):
    updated_category = service.update_category(id, category_in)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return {
        "id": updated_category["id"],
        "name": updated_category["name"],
        "updatedAt": updated_category["updatedAt"]
    }

@router.delete("/{id}")
def delete_category(id: str, service: CategoryService = Depends(get_category_service)):
    success = service.delete_category(id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}
