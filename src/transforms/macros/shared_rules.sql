{% macro order_filter() %}
    {# Mirrors src/shared_logic/rules.py ORDER_VALIDATIONS #}
    order_id IS NOT NULL
    AND customer_id IS NOT NULL
    AND amount > 0
{% endmacro %}

{% macro is_completed(column='status') %}
    {# Mirrors COMPLETED_STATUSES in shared_logic/rules.py #}
    {{ column }} IN ('delivered', 'completed')
{% endmacro %}

{% macro is_cancelled(column='status') %}
    {# Mirrors CANCELLED_STATUSES in shared_logic/rules.py #}
    {{ column }} IN ('cancelled', 'returned')
{% endmacro %}

{% macro inventory_alert(qty_col='qty_available', safety_col='safety_stock', reorder_col='reorder_point') %}
    {# Mirrors INVENTORY_ALERT_RULES in shared_logic/rules.py #}
    CASE
        WHEN {{ qty_col }} <= 0 THEN 'OUT_OF_STOCK'
        WHEN {{ qty_col }} <= {{ safety_col }} THEN 'LOW_STOCK'
        WHEN {{ qty_col }} <= {{ reorder_col }} THEN 'REORDER'
        ELSE NULL
    END
{% endmacro %}

{% macro reconciliation_alert(discrepancy_col='discrepancy_pct') %}
    {# Mirrors PAYMENT_RECONCILIATION_THRESHOLD_PCT (1.0%) in shared_logic/rules.py #}
    CASE
        WHEN {{ discrepancy_col }} > 3.0 THEN 'CRITICAL'
        WHEN {{ discrepancy_col }} > 1.0 THEN 'WARNING'
        ELSE 'OK'
    END
{% endmacro %}

{% macro phone_normalize(column='phone') %}
    {# Mirrors phone_normalize_sql() in shared_logic/sql_templates.py #}
    CASE
        WHEN {{ column }} LIKE '+84%' THEN '0' || SUBSTR(REPLACE(REPLACE({{ column }}, ' ', ''), '-', ''), 4)
        WHEN {{ column }} LIKE '84%' AND LENGTH(REPLACE(REPLACE({{ column }}, ' ', ''), '-', '')) >= 11
            THEN '0' || SUBSTR(REPLACE(REPLACE({{ column }}, ' ', ''), '-', ''), 3)
        ELSE REPLACE(REPLACE({{ column }}, ' ', ''), '-', '')
    END
{% endmacro %}
