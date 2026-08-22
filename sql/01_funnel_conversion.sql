-- Session-Level Conversion Funnel & Drop-off Diagnostics
WITH session_events_matrix AS (
    SELECT
        e.session_id,
        e.user_id,
        u.city_tier,
        u.acquisition_channel,
        MAX(CASE WHEN e.event_name = 'search' THEN 1 ELSE 0 END) AS has_search,
        MAX(CASE WHEN e.event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN e.event_name = 'checkout_start' THEN 1 ELSE 0 END) AS has_checkout,
        MAX(CASE WHEN e.event_name = 'order_placed' THEN 1 ELSE 0 END) AS has_order
    FROM fct_order_events e
    JOIN dim_users u ON e.user_id = u.user_id
    GROUP BY 
        e.session_id, 
        e.user_id, 
        u.city_tier, 
        u.acquisition_channel
),
aggregated_funnel AS (
    SELECT
        city_tier,
        acquisition_channel,
        COUNT(DISTINCT session_id) AS total_sessions,
        SUM(has_search) AS step_1_searches,
        SUM(has_cart) AS step_2_carts,
        SUM(has_checkout) AS step_3_checkouts,
        SUM(has_order) AS step_4_orders
    FROM session_events_matrix
    GROUP BY 
        city_tier, 
        acquisition_channel
)
SELECT
    city_tier,
    acquisition_channel,
    total_sessions,
    step_1_searches,
    step_2_carts,
    step_3_checkouts,
    step_4_orders,
    -- Step-over-Step Stage Conversion Rates (%)
    ROUND(step_2_carts * 100.0 / NULLIF(step_1_searches, 0), 2) AS search_to_cart_cvr_pct,
    ROUND(step_3_checkouts * 100.0 / NULLIF(step_2_carts, 0), 2) AS cart_to_checkout_cvr_pct,
    ROUND(step_4_orders * 100.0 / NULLIF(step_3_checkouts, 0), 2) AS checkout_to_order_cvr_pct,
    -- Top of Funnel (Overall Conversion %)
    ROUND(step_4_orders * 100.0 / NULLIF(total_sessions, 0), 2) AS session_to_order_cvr_pct
FROM aggregated_funnel
ORDER BY 
    city_tier ASC, 
    session_to_order_cvr_pct DESC;