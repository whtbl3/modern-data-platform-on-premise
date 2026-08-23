/*
    Customer-level order metrics — used for RFM scoring and LTV.
*/

WITH orders AS (
    SELECT * FROM {{ ref('int_orders_all_channels') }}
    WHERE status NOT IN ('cancelled', 'returned')
),

metrics AS (
    SELECT
        customer_uid,
        COUNT(*) AS total_orders,
        COUNT(DISTINCT channel) AS channels_used,
        SUM(total_amount_vnd) AS lifetime_revenue_vnd,
        AVG(total_amount_vnd) AS avg_order_value_vnd,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date,
        DATE_DIFF('day', MIN(order_date), MAX(order_date)) AS tenure_days,
        DATE_DIFF('day', MAX(order_date), CURRENT_DATE) AS days_since_last_order,
        COUNT(CASE WHEN channel = 'pos' THEN 1 END) AS pos_orders,
        COUNT(CASE WHEN channel = 'ecommerce' THEN 1 END) AS ecom_orders
    FROM orders
    WHERE customer_uid IS NOT NULL
    GROUP BY customer_uid
)

SELECT * FROM metrics
