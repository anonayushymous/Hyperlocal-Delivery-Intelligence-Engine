import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_sales_summary(db: Session) -> dict:
    query = text("""
        SELECT 
            COUNT(DISTINCT order_id) AS total_orders,
            COALESCE(SUM(order_value + delivery_fee + surge_fee), 0.0) AS total_sales,
            COALESCE(AVG(order_value), 0.0) AS avg_bill,
            COALESCE(SUM(surge_fee), 0.0) AS surge_money,
            COALESCE(AVG(delivery_time_mins), 0.0) AS avg_time,
            COALESCE(ROUND(SUM(CASE WHEN status = 'delivered' THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(order_id), 0), 1), 0.0) AS success_rate
        FROM fct_orders;
    """)
    df = pd.read_sql(query, db.bind)
    return df.iloc[0].to_dict()

def get_customer_funnel(db: Session) -> list[dict]:
    query = text("""
        WITH stages AS (
            SELECT
                session_id,
                MAX(CASE WHEN event_name = 'search' THEN 1 ELSE 0 END) AS s1,
                MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS s2,
                MAX(CASE WHEN event_name = 'checkout_start' THEN 1 ELSE 0 END) AS s3,
                MAX(CASE WHEN event_name = 'order_placed' THEN 1 ELSE 0 END) AS s4
            FROM fct_order_events
            GROUP BY session_id
        )
        SELECT
            COALESCE(SUM(s1), 0) AS "1. Searched Item",
            COALESCE(SUM(s2), 0) AS "2. Added to Cart",
            COALESCE(SUM(s3), 0) AS "3. Clicked Checkout",
            COALESCE(SUM(s4), 0) AS "4. Paid & Placed Order"
        FROM stages;
    """)
    df = pd.read_sql(query, db.bind)
    if df.empty:
        return []
    return [{"stage": col, "count": int(df.iloc[0][col])} for col in df.columns]

def get_store_delays(db: Session) -> list[dict]:
    query = text("""
        SELECT 
            o.dark_store_id AS store_id,
            s.zone AS location_name,
            s.lat,
            s.lon,
            COUNT(o.order_id) AS total_orders,
            ROUND(AVG(o.delivery_time_mins)::numeric, 1) AS average_delivery_time_mins,
            SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1 ELSE 0 END) AS late_deliveries,
            ROUND(SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(o.order_id), 0), 1) AS late_rate_pct
        FROM fct_orders o
        JOIN dim_dark_stores s ON o.dark_store_id = s.dark_store_id
        WHERE o.status = 'delivered'
        GROUP BY o.dark_store_id, s.zone, s.lat, s.lon
        ORDER BY late_rate_pct DESC;
    """)
    df = pd.read_sql(query, db.bind)
    return df.to_dict(orient="records")

def get_rider_performance(db: Session) -> list[dict]:
    query = text("""
        SELECT 
            r.rider_id,
            r.vehicle_type AS vehicle,
            r.rating,
            COUNT(o.order_id) AS deliveries_completed,
            ROUND(AVG(o.delivery_time_mins)::numeric, 1) AS avg_delivery_speed_mins,
            ROUND(SUM(CASE WHEN o.delivery_time_mins <= o.sla_target_mins THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(o.order_id), 0), 1) AS on_time_rate_pct
        FROM fct_orders o
        JOIN dim_riders r ON o.rider_id = r.rider_id
        WHERE o.status = 'delivered'
        GROUP BY r.rider_id, r.vehicle_type, r.rating
        ORDER BY deliveries_completed DESC
        LIMIT 15;
    """)
    df = pd.read_sql(query, db.bind)
    return df.to_dict(orient="records")