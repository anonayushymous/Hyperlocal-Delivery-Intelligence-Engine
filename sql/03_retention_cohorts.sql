-- User Month-over-Month Retention Cohort Matrix
WITH user_first_purchase AS (
    SELECT
        user_id,
        DATE_TRUNC('month', MIN(placed_at)) AS cohort_month
    FROM fct_orders
    WHERE status = 'delivered'
    GROUP BY user_id
),
user_monthly_activity AS (
    SELECT
        o.user_id,
        ufp.cohort_month,
        DATE_TRUNC('month', o.placed_at) AS order_month,
        -- Calculate relative elapsed month period index (Month 0, Month 1, Month 2, ...)
        (
            (EXTRACT(YEAR FROM o.placed_at) - EXTRACT(YEAR FROM ufp.cohort_month)) * 12 +
            (EXTRACT(MONTH FROM o.placed_at) - EXTRACT(MONTH FROM ufp.cohort_month))
        )::INT AS period_month_offset
    FROM fct_orders o
    JOIN user_first_purchase ufp ON o.user_id = ufp.user_id
    WHERE o.status = 'delivered'
),
cohort_aggregations AS (
    SELECT
        TO_CHAR(cohort_month, 'YYYY-MM') AS signup_cohort,
        COUNT(DISTINCT user_id) AS base_cohort_size,
        COUNT(DISTINCT CASE WHEN period_month_offset = 0 THEN user_id END) AS month_0_retained,
        COUNT(DISTINCT CASE WHEN period_month_offset = 1 THEN user_id END) AS month_1_retained,
        COUNT(DISTINCT CASE WHEN period_month_offset = 2 THEN user_id END) AS month_2_retained,
        COUNT(DISTINCT CASE WHEN period_month_offset = 3 THEN user_id END) AS month_3_retained,
        COUNT(DISTINCT CASE WHEN period_month_offset = 4 THEN user_id END) AS month_4_retained,
        COUNT(DISTINCT CASE WHEN period_month_offset = 5 THEN user_id END) AS month_5_retained
    FROM user_monthly_activity
    GROUP BY cohort_month
)
SELECT
    signup_cohort,
    base_cohort_size,
    -- Absolute Retention Counts
    month_0_retained AS m0_users,
    month_1_retained AS m1_users,
    month_2_retained AS m2_users,
    month_3_retained AS m3_users,
    month_4_retained AS m4_users,
    month_5_retained AS m5_users,
    -- Retention Percentages (%)
    100.0 AS m0_retention_pct,
    ROUND((month_1_retained * 100.0 / NULLIF(base_cohort_size, 0))::NUMERIC, 1) AS m1_retention_pct,
    ROUND((month_2_retained * 100.0 / NULLIF(base_cohort_size, 0))::NUMERIC, 1) AS m2_retention_pct,
    ROUND((month_3_retained * 100.0 / NULLIF(base_cohort_size, 0))::NUMERIC, 1) AS m3_retention_pct,
    ROUND((month_4_retained * 100.0 / NULLIF(base_cohort_size, 0))::NUMERIC, 1) AS m4_retention_pct,
    ROUND((month_5_retained * 100.0 / NULLIF(base_cohort_size, 0))::NUMERIC, 1) AS m5_retention_pct
FROM cohort_aggregations
ORDER BY signup_cohort ASC;