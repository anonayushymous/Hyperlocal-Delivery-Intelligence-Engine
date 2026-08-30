from typing import Optional
from pydantic import BaseModel

class SalesSummary(BaseModel):
    total_orders: int
    total_sales: float
    avg_bill: float
    surge_money: float
    avg_time: float
    success_rate: float

class FunnelStep(BaseModel):
    stage: str
    count: int

class StorePerformance(BaseModel):
    store_id: str
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    total_orders: int
    average_delivery_time_mins: float
    late_deliveries: int
    late_rate_pct: float

class RiderPerformance(BaseModel):
    rider_id: str
    vehicle: str
    rating: float
    deliveries_completed: int
    avg_delivery_speed_mins: float
    on_time_rate_pct: float