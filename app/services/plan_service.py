from fastapi import HTTPException, status
from app.repositories.plan_repository import PlanRepository
from app.schemas.plan_schemas import (
    PlanResponse,
    PlanCreateRequest,
    PlanUpdateRequest,
    PlanToggleResponse
)

class PlanService:
    """
    Business logic for subscription plans.
    """

    def __init__(self):
        self.repo = PlanRepository()

    def list_plans(self, user_id: int) -> list[PlanResponse]:
        plans = self.repo.get_all_plans(user_id)
        return [self._to_response(plan) for plan in plans]

    def get_plan(self, user_id: int, plan_id: int) -> PlanResponse:
        plan = self.repo.get_plan_by_id(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
        return self._to_response(plan)

    def create_plan(self, user_id: int, payload: PlanCreateRequest) -> PlanResponse:
        plan_data = payload.model_dump()
        plan_data["features"] = ",".join(plan_data.get("features") or [])
        plan = self.repo.create_plan(plan_data, user_id)
        return self._to_response(plan)

    def update_plan(self, user_id: int, plan_id: int, payload: PlanUpdateRequest) -> PlanResponse:
        update_data = payload.model_dump(exclude_unset=True)
        if "features" in update_data and update_data["features"] is not None:
            update_data["features"] = ",".join(update_data["features"])
        plan = self.repo.update_plan(plan_id, user_id, update_data)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
        return self._to_response(plan)

    def delete_plan(self, user_id: int, plan_id: int) -> dict:
        if not self.repo.delete_plan(plan_id, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
        return {"message": "Plan deleted successfully"}

    def toggle_plan(self, user_id: int, plan_id: int) -> PlanToggleResponse:
        plan = self.repo.toggle_plan_active(plan_id, user_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
        return PlanToggleResponse(id=plan.id, active=plan.active, updated_at=plan.updated_at)

    def _to_response(self, plan) -> PlanResponse:
        features = plan.features.split(",") if plan.features else []
        return PlanResponse(
            id=plan.id,
            name=plan.name,
            price=plan.price,
            period=plan.period,
            description=plan.description,
            features=[feature for feature in features if feature],
            active=plan.active,
            popular=plan.popular,
            subscribers=plan.subscribers,
            monthly_revenue=plan.monthly_revenue,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
