/*
    Daily store performance scorecard.
    Answers: "Cửa hàng nào đang tốt/kém? So với target thế nào?"
    Used by: Regional Managers (mỗi sáng check trên Superset)
*/

WITH revenue AS (
    SELECT * FROM {{ ref('fct_revenue_daily') }}
    WHERE channel = 'pos'
),

stores AS (
    SELECT * FROM {{ ref('dim_stores') }}
),

daily_store AS (
    SELECT
        r.date_key,
        r.store_id,
        s.store_name,
        s.region,
        s.region_vi,
        s.city,
        s.store_size,
        s.staff_count,
        r.total_orders,
        r.unique_customers,
        r.total_revenue_vnd,
        r.net_revenue_vnd,
        r.avg_order_value_vnd,
        r.total_items_sold,
        -- Productivity metrics
        r.total_revenue_vnd / NULLIF(s.staff_count, 0) AS revenue_per_staff_vnd,
        r.total_revenue_vnd / NULLIF(s.sqm, 0) AS revenue_per_sqm_vnd,
        r.total_orders / NULLIF(s.staff_count, 0) AS orders_per_staff
    FROM revenue r
    LEFT JOIN stores s ON r.store_id = s.store_id
),

with_ranking AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY date_key, region ORDER BY total_revenue_vnd DESC) AS rank_in_region,
        RANK() OVER (PARTITION BY date_key ORDER BY total_revenue_vnd DESC) AS rank_overall
    FROM daily_store
)

SELECT * FROM with_ranking
