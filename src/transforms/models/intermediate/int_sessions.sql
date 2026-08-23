/*
    Clickstream session aggregation — one row per session.
*/

WITH events AS (
    SELECT * FROM {{ ref('stg_clickstream__events') }}
),

sessions AS (
    SELECT
        session_id,
        ecom_customer_id,
        device_type,
        browser,
        os,
        country,
        city,
        referrer,
        utm_campaign,
        utm_source,
        utm_medium,
        COUNT(*) AS total_events,
        SUM(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) AS page_views,
        SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS add_to_carts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
        SUM(CASE WHEN event_type = 'search' THEN 1 ELSE 0 END) AS searches,
        SUM(duration_ms) AS total_duration_ms,
        MIN(event_time) AS session_start,
        MAX(event_time) AS session_end,
        DATE_DIFF('second', MIN(event_time), MAX(event_time)) AS session_duration_sec,
        purchases > 0 AS has_conversion,
        MIN(event_date) AS session_date
    FROM events
    GROUP BY
        session_id, ecom_customer_id, device_type, browser, os,
        country, city, referrer, utm_campaign, utm_source, utm_medium
)

SELECT * FROM sessions
