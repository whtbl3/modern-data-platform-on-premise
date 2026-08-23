WITH source AS (
    SELECT * FROM {{ source('raw_payments', 'payments_vnpay') }}
),

renamed AS (
    SELECT
        vnp_txn_ref AS payment_id,
        vnp_order_info AS order_ref,
        'vnpay' AS gateway,
        CAST(vnp_amount AS BIGINT) AS amount_vnd,
        0 AS fee_vnd,
        CASE vnp_response_code
            WHEN '00' THEN 'success'
            WHEN '07' THEN 'fraud_suspected'
            WHEN '09' THEN 'failed'
            ELSE 'unknown'
        END AS status,
        vnp_bank_code AS bank_code,
        CAST(vnp_pay_date AS TIMESTAMP) AS paid_at,
        CAST(vnp_pay_date AS DATE) AS payment_date
    FROM source
    WHERE vnp_txn_ref IS NOT NULL
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
