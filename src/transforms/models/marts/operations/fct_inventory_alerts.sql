/*
    Inventory alerts — stockout risk per store × SKU.
    Answers: "Sản phẩm nào sắp hết? Cửa hàng nào cần nhập thêm?"
    Alert when qty_available < safety_stock_threshold.
*/

WITH current_stock AS (
    SELECT * FROM {{ ref('stg_inventory__stock_levels') }}
),

latest_snapshot AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY store_id, sku
            ORDER BY snapshot_time DESC
        ) AS _rn
    FROM current_stock
),

products AS (
    SELECT * FROM {{ ref('dim_products') }}
),

stores AS (
    SELECT * FROM {{ ref('dim_stores') }}
),

alerts AS (
    SELECT
        ls.snapshot_date AS date_key,
        ls.store_id,
        s.store_name,
        s.region,
        ls.sku,
        p.product_name,
        p.category_l1,
        ls.qty_on_hand,
        ls.qty_reserved,
        ls.qty_available,
        ls.safety_stock_threshold,
        ls.reorder_point,
        CASE
            WHEN ls.qty_available <= 0 THEN 'OUT_OF_STOCK'
            WHEN ls.qty_available < ls.safety_stock_threshold THEN 'LOW_STOCK'
            WHEN ls.qty_available < ls.reorder_point THEN 'REORDER_NEEDED'
            ELSE 'OK'
        END AS stock_status,
        CASE
            WHEN ls.qty_available <= 0 THEN 'Critical'
            WHEN ls.qty_available < ls.safety_stock_threshold THEN 'High'
            WHEN ls.qty_available < ls.reorder_point THEN 'Medium'
            ELSE 'Low'
        END AS alert_severity
    FROM latest_snapshot ls
    LEFT JOIN products p ON ls.product_id = p.product_id
    LEFT JOIN stores s ON ls.store_id = s.store_id
    WHERE ls._rn = 1
      AND ls.qty_available < ls.reorder_point
)

SELECT * FROM alerts
