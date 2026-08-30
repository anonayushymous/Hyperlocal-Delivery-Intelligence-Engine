from sqlalchemy import Column, Integer, Float, String, DateTime, PrimaryKeyConstraint
from app.database import Base

class DimUser(Base):
    __tablename__ = "dim_users"
    user_id = Column(String, primary_key=True, index=True)
    signup_at = Column(DateTime, nullable=False)
    city_tier = Column(String)
    experiment_group = Column(String)

class DimDarkStore(Base):
    __tablename__ = "dim_dark_stores"
    dark_store_id = Column(String, primary_key=True, index=True)
    zone = Column(String, nullable=False)
    capacity_orders_per_hr = Column(Integer)
    lat = Column(Float)
    lon = Column(Float)

class DimRider(Base):
    __tablename__ = "dim_riders"
    rider_id = Column(String, primary_key=True, index=True)
    dark_store_id = Column(String)
    rating = Column(Float)
    vehicle_type = Column(String)

class DimSKU(Base):
    __tablename__ = "dim_skus"
    sku_id = Column(String, primary_key=True, index=True)
    sku_name = Column(String)
    category = Column(String)
    cost_price = Column(Float)
    selling_price = Column(Float)

class FctInventory(Base):
    __tablename__ = "fct_inventory"
    dark_store_id = Column(String, nullable=False)
    sku_id = Column(String, nullable=False)
    stock_on_hand = Column(Integer)
    reorder_threshold = Column(Integer)
    is_out_of_stock = Column(Integer)
    __table_args__ = (PrimaryKeyConstraint("dark_store_id", "sku_id"),)

class FctOrder(Base):
    __tablename__ = "fct_orders"
    order_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    dark_store_id = Column(String, index=True)
    rider_id = Column(String, index=True)
    placed_at = Column(DateTime, nullable=False)
    order_value = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    surge_fee = Column(Float, default=0.0)
    delivery_time_mins = Column(Float)
    sla_target_mins = Column(Float, default=12.0)
    status = Column(String, index=True)
    failure_reason = Column(String, nullable=True)
    complaint_reason = Column(String, nullable=True)

class FctOrderEvent(Base):
    __tablename__ = "fct_order_events"
    event_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_id = Column(String, index=True)
    event_name = Column(String, index=True)
    event_timestamp = Column(DateTime, nullable=False)