WITH source AS (
    SELECT * FROM {{ source('raw_pos', 'pos_transactions') }}
),

renamed AS (
    SELECT
        txn_id,
        store_id,
        customer_phone,
        cashier_id,
        CAST(total_amount AS BIGINT) AS total_amount_vnd,
        CAST(discount_amount AS BIGINT) AS discount_amount_vnd,
        CAST(tax_amount AS BIGINT) AS tax_amount_vnd,
        payment_method,
        num_items,
        items,
        CAST(txn_timestamp AS TIMESTAMP) AS txn_timestamp,
        CAST(txn_timestamp AS DATE) AS txn_date
    FROM source
    WHERE txn_id IS NOT NULL
      AND total_amount > 0
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY txn_id
            ORDER BY txn_timestamp DESC
        ) AS _row_num
    FROM renamed
)

SELECT * EXCEPT(_row_num)
FROM deduplicated
WHERE _row_num = 1
