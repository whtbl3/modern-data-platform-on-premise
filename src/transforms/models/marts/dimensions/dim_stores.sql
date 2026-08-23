/*
    Store dimension — 120 retail stores.
    Loaded from seed file (slowly changing, updated manually).
*/

SELECT
    store_id,
    store_name,
    region,
    city,
    district,
    address,
    store_format,
    sqm,
    staff_count,
    opened_date,
    manager_name,
    CASE region
        WHEN 'North' THEN 'Miền Bắc'
        WHEN 'Central' THEN 'Miền Trung'
        WHEN 'South' THEN 'Miền Nam'
    END AS region_vi,
    CASE
        WHEN sqm >= 1000 THEN 'Large'
        WHEN sqm >= 500 THEN 'Medium'
        ELSE 'Small'
    END AS store_size
FROM {{ ref('seed_stores') }}
