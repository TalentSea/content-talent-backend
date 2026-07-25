from fastapi import APIRouter, Depends, status
from app.dependencies import get_current_user
from app.schemas.plan_schemas import (
    PlanResponse,
    PlanCreateRequest,
    PlanUpdateRequest,
    PlanToggleResponse
)
from app.services.plan_service import PlanService

router = APIRouter(prefix="/api/v1/plans", tags=["Plans"])
plan_service = PlanService()

@router.get("", response_model=list[PlanResponse], status_code=status.HTTP_200_OK)
def list_plans(current_user: dict = Depends(get_current_user)):
    return plan_service.list_plans(current_user["user_id"])

@router.get("/{plan_id}", response_model=PlanResponse, status_code=status.HTTP_200_OK)
def get_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    return plan_service.get_plan(current_user["user_id"], plan_id)

@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreateRequest, current_user: dict = Depends(get_current_user)):
    return plan_service.create_plan(current_user["user_id"], payload)

@router.put("/{plan_id}", response_model=PlanResponse, status_code=status.HTTP_200_OK)
def update_plan(plan_id: int, payload: PlanUpdateRequest, current_user: dict = Depends(get_current_user)):
    return plan_service.update_plan(current_user["user_id"], plan_id, payload)

@router.delete("/{plan_id}", status_code=status.HTTP_200_OK)
def delete_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    return plan_service.delete_plan(current_user["user_id"], plan_id)

@router.patch("/{plan_id}/toggle", response_model=PlanToggleResponse, status_code=status.HTTP_200_OK)
def toggle_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    return plan_service.toggle_plan(current_user["user_id"], plan_id)
