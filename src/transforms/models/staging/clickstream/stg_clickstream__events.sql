WITH source AS (
    SELECT * FROM {{ source('raw_clickstream', 'clickstream_events') }}
),

renamed AS (
    SELECT
        event_id,
        session_id,
        user_id AS ecom_customer_id,
        event_type,
        page_url,
        referrer,
        utm_campaign,
        utm_source,
        utm_medium,
        device_type,
        browser,
        os,
        country,
        city,
        CAST(duration_ms AS INTEGER) AS duration_ms,
        CAST(event_time AS TIMESTAMP) AS event_time,
        CAST(event_time AS DATE) AS event_date
    FROM source
    WHERE event_id IS NOT NULL
      AND session_id IS NOT NULL
      AND event_type IS NOT NULL
)

SELECT * FROM renamed
