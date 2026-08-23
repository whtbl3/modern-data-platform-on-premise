/*
    Monthly revenue rollup with MoM growth.
    Answers: "Tháng này vs tháng trước tăng/giảm bao nhiêu %?"
*/

WITH daily AS (
    SELECT * FROM {{ ref('fct_revenue_daily') }}
),

monthly AS (
    SELECT
        DATE_TRUNC('month', date_key) AS month_key,
        SUM(total_orders) AS total_orders,
        SUM(unique_customers) AS unique_customers,
        SUM(total_revenue_vnd) AS total_revenue_vnd,
        SUM(net_revenue_vnd) AS net_revenue_vnd,
        SUM(total_revenue_vnd) / NULLIF(SUM(total_orders), 0) AS avg_order_value_vnd
    FROM daily
    GROUP BY DATE_TRUNC('month', date_key)
),

with_growth AS (
    SELECT
        *,
        LAG(total_revenue_vnd) OVER (ORDER BY month_key) AS prev_month_revenue_vnd,
        (total_revenue_vnd - LAG(total_revenue_vnd) OVER (ORDER BY month_key))
            / NULLIF(LAG(total_revenue_vnd) OVER (ORDER BY month_key), 0) AS mom_growth_rate
    FROM monthly
)

SELECT * FROM with_growth
