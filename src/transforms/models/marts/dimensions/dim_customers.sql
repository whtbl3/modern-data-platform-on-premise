/*
    Customer dimension with RFM segmentation.
    Combines identity resolution + order metrics.
    Updated daily.
*/

WITH unified AS (
    SELECT * FROM {{ ref('int_customers_unified') }}
),

metrics AS (
    SELECT * FROM {{ ref('int_customer_metrics') }}
),

rfm_scored AS (
    SELECT
        u.customer_uid,
        u.customer_name,
        u.email,
        u.phone_normalized,
        u.ecom_customer_id,
        u.loyalty_member_id,
        u.customer_type,
        u.is_omnichannel,
        u.first_seen_at,
        m.total_orders,
        m.lifetime_revenue_vnd,
        m.avg_order_value_vnd,
        m.first_order_date,
        m.last_order_date,
        m.days_since_last_order,
        m.tenure_days,
        m.channels_used,
        m.pos_orders,
        m.ecom_orders,
        NTILE(5) OVER (ORDER BY m.days_since_last_order ASC) AS recency_score,
        NTILE(5) OVER (ORDER BY m.total_orders ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY m.lifetime_revenue_vnd ASC) AS monetary_score
    FROM unified u
    LEFT JOIN metrics m ON u.customer_uid = m.customer_uid
),

segmented AS (
    SELECT
        *,
        recency_score + frequency_score + monetary_score AS rfm_total,
        CASE
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champion'
            WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal'
            WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customer'
            WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
            WHEN recency_score <= 2 AND frequency_score <= 2 AND monetary_score >= 3 THEN 'Hibernating'
            WHEN recency_score <= 1 THEN 'Lost'
            ELSE 'Regular'
        END AS rfm_segment
    FROM rfm_scored
)

SELECT * FROM segmented
