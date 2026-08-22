-- Micro-Market Rolling SLA Breach & Turnaround Time Percentiles
WITH daily_store_fulfillments AS (
    SELECT
        o.dark_store_id,
        d.zone,
        DATE_TRUNC('day', o.placed_at)::DATE AS metric_date,
        COUNT(o.order_id) AS total_daily_orders,
        AVG(o.delivery_time_mins) AS avg_daily_delivery_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY o.delivery_time_mins) AS p95_delivery_time,
        SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1 ELSE 0 END) AS total_sla_breaches
    FROM fct_orders o
    JOIN dim_dark_stores d ON o.dark_store_id = d.dark_store_id
    WHERE o.status = 'delivered'
    GROUP BY 
        o.dark_store_id, 
        d.zone, 
        DATE_TRUNC('day', o.placed_at)::DATE
)
SELECT
    dark_store_id,
    zone,
    metric_date,
    total_daily_orders,
    ROUND(avg_daily_delivery_time::NUMERIC, 2) AS avg_daily_delivery_time,
    ROUND(p95_delivery_time::NUMERIC, 2) AS p95_delivery_time,
    total_sla_breaches,
    ROUND((total_sla_breaches * 100.0 / NULLIF(total_daily_orders, 0))::NUMERIC, 2) AS daily_breach_rate_pct,
    -- 7-Day Rolling Moving Average of SLA Breach Rate (%)
    ROUND(
        AVG(total_sla_breaches * 100.0 / NULLIF(total_daily_orders, 0)) OVER (
            PARTITION BY dark_store_id 
            ORDER BY metric_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::NUMERIC, 
        2
    ) AS rolling_7d_avg_breach_rate_pct,
    -- 7-Day Rolling Cumulative Orders
    SUM(total_daily_orders) OVER (
        PARTITION BY dark_store_id 
        ORDER BY metric_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_total_orders
FROM daily_store_fulfillments
ORDER BY 
    dark_store_id, 
    metric_date DESC;