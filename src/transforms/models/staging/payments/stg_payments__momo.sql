WITH source AS (
    SELECT * FROM {{ source('raw_payments', 'payments_momo') }}
),

renamed AS (
    SELECT
        trans_id AS payment_id,
        order_id AS order_ref,
        'momo' AS gateway,
        CAST(amount AS BIGINT) AS amount_vnd,
        0 AS fee_vnd,
        CASE result_code
            WHEN 0 THEN 'success'
            WHEN 1006 THEN 'user_cancelled'
            ELSE 'failed'
        END AS status,
        NULL AS bank_code,
        CAST(response_time AS TIMESTAMP) AS paid_at,
        CAST(response_time AS DATE) AS payment_date
    FROM source
    WHERE trans_id IS NOT NULL
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY payment_id ORDER BY paid_at DESC) AS _row_num
    FROM renamed
)

SELECT * EXCEPT(_row_num)
FROM deduplicated
WHERE _row_num = 1
