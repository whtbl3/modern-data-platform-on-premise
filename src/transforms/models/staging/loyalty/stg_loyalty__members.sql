WITH source AS (
    SELECT * FROM {{ source('raw_loyalty', 'loyalty_members') }}
),

renamed AS (
    SELECT
        member_id AS loyalty_member_id,
        full_name,
        LOWER(TRIM(email)) AS email,
        REGEXP_REPLACE(phone, '[^0-9]', '') AS phone_raw,
        tier,
        points_balance,
        CAST(joined_date AS TIMESTAMP) AS joined_at,
        CAST(last_activity_date AS TIMESTAMP) AS last_activity_at,
        CAST(updated_at AS TIMESTAMP) AS updated_at
    FROM source
    WHERE member_id IS NOT NULL
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
)

SELECT * FROM normalized
