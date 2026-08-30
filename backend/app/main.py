from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.schemas import SalesSummary, FunnelStep, StorePerformance, RiderPerformance
from app.services.analytics import get_sales_summary, get_customer_funnel, get_store_delays, get_rider_performance

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hyperlocal Delivery Intelligence API",
    version="2.0.0",
    description="Microservice engine for real-time delivery telemetry, KPIs, and operational intelligence."
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Hyperlocal Delivery Intelligence API"}

@app.get("/api/v1/metrics/sales-summary", response_model=SalesSummary)
def api_sales_summary(db: Session = Depends(get_db)):
    return get_sales_summary(db)

@app.get("/api/v1/metrics/funnel", response_model=List[FunnelStep])
def api_funnel(db: Session = Depends(get_db)):
    return get_customer_funnel(db)

@app.get("/api/v1/metrics/store-delays", response_model=List[StorePerformance])
def api_store_delays(db: Session = Depends(get_db)):
    return get_store_delays(db)

@app.get("/api/v1/metrics/rider-performance", response_model=List[RiderPerformance])
def api_rider_performance(db: Session = Depends(get_db)):
    return get_rider_performance(db)