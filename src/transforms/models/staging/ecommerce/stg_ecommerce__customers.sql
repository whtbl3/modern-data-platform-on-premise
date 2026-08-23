WITH source AS (
    SELECT * FROM {{ source('raw_ecommerce', 'ecom_customers') }}
),

renamed AS (
    SELECT
        customer_id AS ecom_customer_id,
        full_name,
        LOWER(TRIM(email)) AS email,
        REGEXP_REPLACE(phone, '[^0-9]', '') AS phone_raw,
        gender,
        date_of_birth,
        registration_source,
        CAST(created_at AS TIMESTAMP) AS registered_at,
        CAST(updated_at AS TIMESTAMP) AS updated_at
    FROM source
    WHERE customer_id IS NOT NULL
),

normalized AS (
    SELECT
        *,
        CASE
            WHEN phone_raw LIKE '84%' THEN '0' || SUBSTRING(phone_raw, 3)
            WHEN phone_raw LIKE '0%' THEN phone_raw
            ELSE phone_raw
        END AS phone_normalized
    FROM renamed
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY ecom_customer_id
            ORDER BY updated_at DESC
        ) AS _row_num
    FROM normalized
)

SELECT * EXCEPT(_row_num)
FROM deduplicated
WHERE _row_num = 1
