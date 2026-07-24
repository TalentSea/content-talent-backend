from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class SubscriberItemResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    status: str
    revenue: float
    joined_at: datetime
    avatar: Optional[str] = None

class SubscriberProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    status: str
    total_revenue: float
    revenue: float
    joined_at: datetime
    last_active_at: datetime
    avatar: Optional[str] = None

class SubscriberStatsResponse(BaseModel):
    total_subscribers: int
    growth_rate: float
    avg_revenue_per_user: float
    churn_rate: float

class PlanDistributionItem(BaseModel):
    plan: str
    count: int
    percentage: float

class UpdateSubscriberPlanRequest(BaseModel):
    plan: str

class EmailSubscriberRequest(BaseModel):
    subject: str
    body: str

class SuspendSubscriberRequest(BaseModel):
    reason: Optional[str] = None
