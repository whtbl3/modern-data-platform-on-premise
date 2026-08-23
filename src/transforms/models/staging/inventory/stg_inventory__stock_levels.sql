WITH source AS (
    SELECT * FROM {{ source('raw_inventory', 'stock_levels') }}
),

renamed AS (
    SELECT
        store_id,
        sku,
        product_id,
        CAST(quantity_on_hand AS INTEGER) AS qty_on_hand,
        CAST(quantity_reserved AS INTEGER) AS qty_reserved,
        CAST(quantity_on_hand AS INTEGER) - CAST(quantity_reserved AS INTEGER) AS qty_available,
        CAST(safety_stock AS INTEGER) AS safety_stock_threshold,
        CAST(reorder_point AS INTEGER) AS reorder_point,
        CAST(snapshot_time AS TIMESTAMP) AS snapshot_time,
        CAST(snapshot_time AS DATE) AS snapshot_date
    FROM source
    WHERE store_id IS NOT NULL
      AND sku IS NOT NULL
      AND quantity_on_hand >= 0
)

SELECT * FROM renamed
