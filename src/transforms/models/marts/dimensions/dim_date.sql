/*
    Date dimension — every analytics fact joins to this.
    Pre-generated for 5 years: 2022-01-01 to 2026-12-31.
*/

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2022-01-01' as date)",
        end_date="cast('2026-12-31' as date)"
    ) }}
),

enriched AS (
    SELECT
        CAST(date_day AS DATE) AS date_key,
        YEAR(date_day) AS year,
        QUARTER(date_day) AS quarter,
        MONTH(date_day) AS month,
        DAY(date_day) AS day_of_month,
        DAY_OF_WEEK(date_day) AS day_of_week,
        WEEK(date_day) AS week_of_year,
        CASE
            WHEN DAY_OF_WEEK(date_day) IN (1, 7) THEN TRUE
            ELSE FALSE
        END AS is_weekend,
        FORMAT_DATETIME(date_day, 'EEEE') AS day_name,
        FORMAT_DATETIME(date_day, 'MMMM') AS month_name,
        DATE_TRUNC('month', date_day) AS first_day_of_month,
        DATE_TRUNC('quarter', date_day) AS first_day_of_quarter,
        CONCAT(YEAR(date_day), '-Q', QUARTER(date_day)) AS year_quarter,
        CONCAT(YEAR(date_day), '-', LPAD(CAST(MONTH(date_day) AS VARCHAR), 2, '0')) AS year_month
    FROM date_spine
)

SELECT * FROM enriched
