/*
    Three-way revenue reconciliation: POS vs E-commerce vs Payment gateways.
    Answers: "Số liệu có khớp không? Discrepancy ở đâu?"
    Alert if delta > 1%.
*/

WITH pos_revenue AS (
    SELECT
        txn_date AS date_key,
        'pos' AS source,
        SUM(total_amount_vnd) AS total_vnd,
        COUNT(*) AS txn_count
    FROM {{ ref('stg_pos__transactions') }}
    GROUP BY txn_date
),

ecom_revenue AS (
    SELECT
        CAST(order_date AS DATE) AS date_key,
        'ecommerce' AS source,
        SUM(total_amount_vnd) AS total_vnd,
        COUNT(*) AS txn_count
    FROM {{ ref('stg_ecommerce__orders') }}
    WHERE status NOT IN ('cancelled', 'returned')
    GROUP BY CAST(order_date AS DATE)
),

payment_revenue AS (
    SELECT
        payment_date AS date_key,
        'payments' AS source,
        SUM(amount_vnd) AS total_vnd,
        COUNT(*) AS txn_count
    FROM {{ ref('stg_payments__consolidated') }}
    WHERE status = 'success'
    GROUP BY payment_date
),

combined AS (
    SELECT * FROM pos_revenue
    UNION ALL
    SELECT * FROM ecom_revenue
    UNION ALL
    SELECT * FROM payment_revenue
),

pivoted AS (
    SELECT
        date_key,
        SUM(CASE WHEN source = 'pos' THEN total_vnd ELSE 0 END) AS pos_revenue_vnd,
        SUM(CASE WHEN source = 'ecommerce' THEN total_vnd ELSE 0 END) AS ecom_revenue_vnd,
        SUM(CASE WHEN source = 'payments' THEN total_vnd ELSE 0 END) AS payment_revenue_vnd,
        SUM(CASE WHEN source = 'pos' THEN total_vnd ELSE 0 END)
            + SUM(CASE WHEN source = 'ecommerce' THEN total_vnd ELSE 0 END) AS expected_total_vnd
    FROM combined
    GROUP BY date_key
),

with_delta AS (
    SELECT
        *,
        expected_total_vnd - payment_revenue_vnd AS discrepancy_vnd,
        ABS(expected_total_vnd - payment_revenue_vnd)
            / NULLIF(expected_total_vnd, 0) AS discrepancy_pct,
        CASE
            WHEN ABS(expected_total_vnd - payment_revenue_vnd)
                / NULLIF(expected_total_vnd, 0) > 0.01 THEN 'ALERT'
            ELSE 'OK'
        END AS reconciliation_status
    FROM pivoted
)

SELECT * FROM with_delta
