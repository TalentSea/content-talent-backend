from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.dependencies import get_current_user
from app.schemas.subscriber_schemas import (
    SubscriberStatsResponse,
    PlanDistributionItem,
    UpdateSubscriberPlanRequest,
    EmailSubscriberRequest,
    SuspendSubscriberRequest,
    SubscriberProfileResponse,
    SubscriberItemResponse
)
from app.schemas.common_schemas import PaginatedResponse
from app.services.subscriber_service import SubscriberService

router = APIRouter(prefix="/api/v1/subscribers", tags=["Subscribers"])
subscriber_service = SubscriberService()

@router.get("/stats", response_model=SubscriberStatsResponse, status_code=status.HTTP_200_OK)
def subscriber_stats(current_user: dict = Depends(get_current_user)):
    return subscriber_service.get_stats(current_user["user_id"])

@router.get("/plan-distribution", response_model=list[PlanDistributionItem], status_code=status.HTTP_200_OK)
def plan_distribution(current_user: dict = Depends(get_current_user)):
    return subscriber_service.get_plan_distribution(current_user["user_id"])

@router.get("/recent", response_model=list[SubscriberItemResponse], status_code=status.HTTP_200_OK)
def recent_subscribers(limit: int = Query(5, ge=1, le=20), current_user: dict = Depends(get_current_user)):
    return subscriber_service.get_recent_subscribers(current_user["user_id"], limit=limit)

@router.get("", response_model=PaginatedResponse[SubscriberItemResponse], status_code=status.HTTP_200_OK)
def list_subscribers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    plan: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    join_date_from: Optional[datetime] = Query(None),
    join_date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return subscriber_service.list_subscribers(
        current_user["user_id"],
        page=page,
        limit=limit,
        plan=plan,
        status=status_filter,
        join_date_from=join_date_from,
        join_date_to=join_date_to,
        search=search,
    )

@router.get("/{subscriber_id}", response_model=SubscriberProfileResponse, status_code=status.HTTP_200_OK)
def get_subscriber(subscriber_id: int, current_user: dict = Depends(get_current_user)):
    return subscriber_service.get_subscriber(current_user["user_id"], subscriber_id)

@router.put("/{subscriber_id}/plan", response_model=SubscriberProfileResponse, status_code=status.HTTP_200_OK)
def update_subscriber_plan(subscriber_id: int, payload: UpdateSubscriberPlanRequest, current_user: dict = Depends(get_current_user)):
    return subscriber_service.change_plan(current_user["user_id"], subscriber_id, payload)

@router.post("/{subscriber_id}/email", status_code=status.HTTP_200_OK)
def email_subscriber(subscriber_id: int, payload: EmailSubscriberRequest, current_user: dict = Depends(get_current_user)):
    return subscriber_service.send_email(current_user["user_id"], subscriber_id, payload)

@router.put("/{subscriber_id}/suspend", response_model=SubscriberProfileResponse, status_code=status.HTTP_200_OK)
def suspend_subscriber(subscriber_id: int, payload: SuspendSubscriberRequest, current_user: dict = Depends(get_current_user)):
    return subscriber_service.suspend_subscriber(current_user["user_id"], subscriber_id, payload)

@router.put("/{subscriber_id}/reinstate", response_model=SubscriberProfileResponse, status_code=status.HTTP_200_OK)
def reinstate_subscriber(subscriber_id: int, current_user: dict = Depends(get_current_user)):
    return subscriber_service.reinstate_subscriber(current_user["user_id"], subscriber_id)
