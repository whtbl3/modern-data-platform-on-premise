/*
    Product dimension — loaded from seed (master product catalog from SAP).
*/

SELECT
    product_id,
    sku,
    product_name,
    category_l1,
    category_l2,
    brand,
    CAST(price_vnd AS BIGINT) AS price_vnd,
    CAST(cost_vnd AS BIGINT) AS cost_vnd,
    price_vnd - cost_vnd AS margin_vnd,
    CAST((price_vnd - cost_vnd) AS DOUBLE) / NULLIF(price_vnd, 0) AS margin_pct,
    supplier_id,
    supplier_name,
    weight_kg,
    is_active
FROM {{ ref('seed_products') }}
