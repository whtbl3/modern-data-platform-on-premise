/*
    Conversion funnel metrics by day/channel/device.
    Answers: "User drop off ở đâu? Device nào convert tốt nhất?"
*/

WITH sessions AS (
    SELECT * FROM {{ ref('int_sessions') }}
),

funnel AS (
    SELECT
        session_date AS date_key,
        referrer,
        device_type,
        country,
        COUNT(*) AS total_sessions,
        SUM(CASE WHEN page_views > 0 THEN 1 ELSE 0 END) AS sessions_with_view,
        SUM(CASE WHEN searches > 0 THEN 1 ELSE 0 END) AS sessions_with_search,
        SUM(CASE WHEN add_to_carts > 0 THEN 1 ELSE 0 END) AS sessions_with_cart,
        SUM(CASE WHEN has_conversion THEN 1 ELSE 0 END) AS sessions_with_purchase,
        -- Step-by-step rates
        CAST(SUM(CASE WHEN add_to_carts > 0 THEN 1 ELSE 0 END) AS DOUBLE)
            / NULLIF(SUM(CASE WHEN page_views > 0 THEN 1 ELSE 0 END), 0) AS view_to_cart_rate,
        CAST(SUM(CASE WHEN has_conversion THEN 1 ELSE 0 END) AS DOUBLE)
            / NULLIF(SUM(CASE WHEN add_to_carts > 0 THEN 1 ELSE 0 END), 0) AS cart_to_purchase_rate,
        -- Overall
        CAST(SUM(CASE WHEN has_conversion THEN 1 ELSE 0 END) AS DOUBLE)
            / NULLIF(COUNT(*), 0) AS overall_conversion_rate
    FROM sessions
    GROUP BY session_date, referrer, device_type, country
)

SELECT * FROM funnel
