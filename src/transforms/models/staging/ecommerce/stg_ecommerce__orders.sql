WITH source AS (
    SELECT * FROM {{ source('raw_ecommerce', 'ecom_orders') }}
),

renamed AS (
    SELECT
        order_id,
        customer_id AS ecom_customer_id,
        status,
        payment_method,
        num_items,
        CAST(subtotal AS BIGINT) AS subtotal_vnd,
        CAST(discount AS BIGINT) AS discount_vnd,
        CAST(shipping_fee AS BIGINT) AS shipping_fee_vnd,
        CAST(total_amount AS BIGINT) AS total_amount_vnd,
        shipping_address_city,
        shipping_address_district,
        CAST(order_date AS TIMESTAMP) AS order_date,
        CAST(created_at AS TIMESTAMP) AS created_at,
        CAST(updated_at AS TIMESTAMP) AS updated_at
    FROM source
    WHERE order_id IS NOT NULL
      AND total_amount > 0
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY updated_at DESC
        ) AS _row_num
    FROM renamed
)

SELECT * EXCEPT(_row_num)
FROM deduplicated
WHERE _row_num = 1
