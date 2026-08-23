/*
    Daily revenue fact table — the CEO's morning report.
    Grain: date × store × channel × category
    Answers: "Hôm qua bán được bao nhiêu?"
*/

WITH orders AS (
    SELECT * FROM {{ ref('int_orders_all_channels') }}
    WHERE status NOT IN ('cancelled', 'returned')
),

daily AS (
    SELECT
        order_date AS date_key,
        store_id,
        channel,
        COUNT(*) AS total_orders,
        COUNT(DISTINCT customer_uid) AS unique_customers,
        SUM(total_amount_vnd) AS total_revenue_vnd,
        SUM(discount_amount_vnd) AS total_discount_vnd,
        SUM(tax_amount_vnd) AS total_tax_vnd,
        SUM(total_amount_vnd) - SUM(discount_amount_vnd) AS net_revenue_vnd,
        AVG(total_amount_vnd) AS avg_order_value_vnd,
        SUM(num_items) AS total_items_sold
    FROM orders
    GROUP BY order_date, store_id, channel
)

SELECT * FROM daily
