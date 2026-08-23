/*
    Identity Resolution: merge customers across POS, E-commerce, and Loyalty.
    Match by normalized phone OR email. Generates a single customer_uid.
*/

WITH ecom_customers AS (
    SELECT
        ecom_customer_id,
        full_name,
        email,
        phone_normalized,
        registered_at
    FROM {{ ref('stg_ecommerce__customers') }}
),

loyalty_members AS (
    SELECT
        loyalty_member_id,
        full_name,
        email,
        phone_normalized,
        joined_at
    FROM {{ ref('stg_loyalty__members') }}
),

pos_customers AS (
    SELECT DISTINCT
        customer_phone AS phone_normalized
    FROM {{ ref('stg_pos__transactions') }}
    WHERE customer_phone IS NOT NULL
),

-- Step 1: E-commerce as base (has richest profile)
base AS (
    SELECT
        ecom_customer_id,
        full_name,
        email,
        phone_normalized,
        registered_at AS first_seen_at
    FROM ecom_customers
),

-- Step 2: Match loyalty by phone or email
with_loyalty AS (
    SELECT
        b.*,
        l.loyalty_member_id,
        l.joined_at AS loyalty_joined_at
    FROM base b
    LEFT JOIN loyalty_members l
        ON b.phone_normalized = l.phone_normalized
        OR b.email = l.email
),

-- Step 3: Identify POS-only customers (phone match)
with_pos AS (
    SELECT
        wl.*,
        CASE
            WHEN p.phone_normalized IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS has_pos_activity
    FROM with_loyalty wl
    LEFT JOIN pos_customers p
        ON wl.phone_normalized = p.phone_normalized
),

-- Step 4: Generate unified ID and classify
final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['ecom_customer_id', 'phone_normalized']) }} AS customer_uid,
        ecom_customer_id,
        loyalty_member_id,
        full_name AS customer_name,
        email,
        phone_normalized,
        first_seen_at,
        CASE
            WHEN loyalty_member_id IS NOT NULL AND has_pos_activity THEN 'omnichannel'
            WHEN has_pos_activity THEN 'offline_online'
            WHEN loyalty_member_id IS NOT NULL THEN 'online_loyalty'
            ELSE 'online_only'
        END AS customer_type,
        CASE
            WHEN loyalty_member_id IS NOT NULL AND has_pos_activity THEN TRUE
            ELSE FALSE
        END AS is_omnichannel
    FROM with_pos
)

SELECT * FROM final
