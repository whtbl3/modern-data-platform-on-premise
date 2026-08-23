/*
    Campaign performance — attribution and conversion metrics.
    Answers: "Campaign nào hiệu quả? ROI bao nhiêu?"
*/

WITH sessions AS (
    SELECT * FROM {{ ref('int_sessions') }}
    WHERE utm_campaign IS NOT NULL
),

campaign_metrics AS (
    SELECT
        utm_campaign AS campaign,
        utm_source AS source,
        utm_medium AS medium,
        session_date AS date_key,
        COUNT(*) AS total_sessions,
        COUNT(DISTINCT ecom_customer_id) AS unique_visitors,
        SUM(page_views) AS total_page_views,
        SUM(CASE WHEN has_conversion THEN 1 ELSE 0 END) AS conversions,
        CAST(SUM(CASE WHEN has_conversion THEN 1 ELSE 0 END) AS DOUBLE)
            / NULLIF(COUNT(*), 0) AS conversion_rate,
        AVG(session_duration_sec) AS avg_session_duration_sec,
        AVG(page_views) AS avg_pages_per_session,
        SUM(CASE WHEN add_to_carts > 0 THEN 1 ELSE 0 END) AS sessions_with_cart
    FROM sessions
    GROUP BY utm_campaign, utm_source, utm_medium, session_date
)

SELECT * FROM campaign_metrics
