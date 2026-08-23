/*
    Union POS and E-commerce orders into a single fact with unified customer_uid.
    This is the base for all revenue analytics.
*/

WITH pos AS (
    SELECT
        txn_id AS order_id,
        'pos' AS channel,
        t.store_id,
        c.customer_uid,
        t.total_amount_vnd,
        t.discount_amount_vnd,
        t.tax_amount_vnd,
        t.payment_method,
        t.num_items,
        t.txn_timestamp AS order_timestamp,
        t.txn_date AS order_date,
        'completed' AS status
    FROM {{ ref('stg_pos__transactions') }} t
    LEFT JOIN {{ ref('int_customers_unified') }} c
        ON t.customer_phone = c.phone_normalized
),

ecom AS (
    SELECT
        order_id,
        'ecommerce' AS channel,
        NULL AS store_id,
        c.customer_uid,
        e.total_amount_vnd,
        e.discount_vnd AS discount_amount_vnd,
        0 AS tax_amount_vnd,
        e.payment_method,
        e.num_items,
        e.order_date AS order_timestamp,
        CAST(e.order_date AS DATE) AS order_date,
        e.status
    FROM {{ ref('stg_ecommerce__orders') }} e
    LEFT JOIN {{ ref('int_customers_unified') }} c
        ON e.ecom_customer_id = c.ecom_customer_id
),

unioned AS (
    SELECT * FROM pos
    UNION ALL
    SELECT * FROM ecom
)

SELECT * FROM unioned
