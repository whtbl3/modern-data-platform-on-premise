{% macro deduplicate(relation, partition_by, order_by) %}
    SELECT * EXCEPT(_row_num)
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY {{ partition_by }}
                ORDER BY {{ order_by }} DESC
            ) AS _row_num
        FROM {{ relation }}
    )
    WHERE _row_num = 1
{% endmacro %}
