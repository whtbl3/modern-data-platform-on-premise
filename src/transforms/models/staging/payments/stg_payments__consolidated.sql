WITH vnpay AS (
    SELECT * FROM {{ ref('stg_payments__vnpay') }}
),

momo AS (
    SELECT * FROM {{ ref('stg_payments__momo') }}
),

card AS (
    SELECT * FROM {{ ref('stg_payments__card') }}
),

unioned AS (
    SELECT payment_id, order_ref, gateway, amount_vnd, fee_vnd, status, bank_code, paid_at, payment_date FROM vnpay
    UNION ALL
    SELECT payment_id, order_ref, gateway, amount_vnd, fee_vnd, status, bank_code, paid_at, payment_date FROM momo
    UNION ALL
    SELECT payment_id, order_ref, gateway, amount_vnd, fee_vnd, status, bank_code, paid_at, payment_date FROM card
)

SELECT * FROM unioned
