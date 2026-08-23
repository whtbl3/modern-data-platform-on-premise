WITH source AS (
    SELECT * FROM {{ source('raw_payments', 'payments_card') }}
),

renamed AS (
    SELECT
        transaction_id AS payment_id,
        merchant_ref AS order_ref,
        'card' AS gateway,
        CAST(gross_amount AS BIGINT) - CAST(fee AS BIGINT) AS amount_vnd,
        CAST(fee AS BIGINT) AS fee_vnd,
        CASE status
            WHEN 'SETTLED' THEN 'success'
            WHEN 'DECLINED' THEN 'failed'
            WHEN 'REFUNDED' THEN 'refunded'
            ELSE 'pending'
        END AS status,
        issuer_bank AS bank_code,
        CAST(settled_at AS TIMESTAMP) AS paid_at,
        CAST(settled_at AS DATE) AS payment_date
    FROM source
    WHERE transaction_id IS NOT NULL
)

SELECT * FROM renamed
