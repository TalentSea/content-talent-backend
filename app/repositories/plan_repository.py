from datetime import datetime
from typing import List, Optional, Tuple
from app.models.plan import Plan

class PlanRepository:
    """
    Data access layer for subscription plans.
    """

    def create_plan(self, plan_data: dict, user_id: int) -> Plan:
        return Plan.create(user=user_id, **plan_data)

    def get_plan_by_id(self, plan_id: int, user_id: int) -> Optional[Plan]:
        return Plan.get_or_none((Plan.id == plan_id) & (Plan.user == user_id))

    def get_all_plans(self, user_id: int) -> List[Plan]:
        return list(Plan.select().where(Plan.user == user_id).order_by(Plan.created_at.desc()))

    def update_plan(self, plan_id: int, user_id: int, update_data: dict) -> Optional[Plan]:
        plan = self.get_plan_by_id(plan_id, user_id)
        if not plan:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(plan, key, value)
        plan.updated_at = datetime.now()
        plan.save()
        return plan

    def delete_plan(self, plan_id: int, user_id: int) -> bool:
        plan = self.get_plan_by_id(plan_id, user_id)
        if not plan:
            return False
        plan.delete_instance()
        return True

    def toggle_plan_active(self, plan_id: int, user_id: int) -> Optional[Plan]:
        plan = self.get_plan_by_id(plan_id, user_id)
        if not plan:
            return None
        plan.active = not plan.active
        plan.updated_at = datetime.now()
        plan.save()
        return plan
