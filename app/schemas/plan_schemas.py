from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class PlanResponse(BaseModel):
    id: int
    name: str
    price: float
    period: str
    description: Optional[str] = None
    features: List[str] = []
    active: bool
    popular: bool
    subscribers: float
    monthly_revenue: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PlanCreateRequest(BaseModel):
    name: str
    price: float
    period: str
    description: Optional[str] = None
    features: Optional[List[str]] = []
    active: bool = True
    popular: bool = False

class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    period: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    active: Optional[bool] = None
    popular: Optional[bool] = None

class PlanToggleResponse(BaseModel):
    id: int
    active: bool
    updated_at: Optional[datetime] = None
