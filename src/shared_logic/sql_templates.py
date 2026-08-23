"""
SQL templates generated from shared rules.
Used by both Flink (streaming) and dbt macros (batch).

Ensures the same WHERE clauses, CASE expressions, and aggregation
logic runs identically in both paths.
"""
from .rules import (
    CANCELLED_STATUSES,
    COMPLETED_STATUSES,
    ORDER_VALIDATIONS,
    PAYMENT_RECONCILIATION_THRESHOLD_PCT,
    REVENUE_DAILY,
)


def order_filter_sql() -> str:
    """WHERE clause for valid orders — used in both batch and streaming."""
    conditions = [f"{v.field} {v.condition}" for v in ORDER_VALIDATIONS]
    return " AND ".join(conditions)


def is_completed_sql(column: str = "status") -> str:
    statuses = ", ".join(f"'{s}'" for s in COMPLETED_STATUSES)
    return f"{column} IN ({statuses})"


def is_cancelled_sql(column: str = "status") -> str:
    statuses = ", ".join(f"'{s}'" for s in CANCELLED_STATUSES)
    return f"{column} IN ({statuses})"


def revenue_aggregation_sql(source: str = "orders", where: str | None = None) -> str:
    """Full revenue aggregation query — works in Flink SQL and Trino."""
    rule = REVENUE_DAILY
    metrics = ",\n        ".join(f"{expr} AS {name}" for name, expr in rule.metrics.items())
    group_by = ", ".join(rule.group_by)
    where_clause = f"\n    WHERE {where}" if where else ""

    return f"""
    SELECT
        {group_by},
        {metrics}
    FROM {source}{where_clause}
    GROUP BY {group_by}
    """


def inventory_alert_case_sql(qty_col: str = "qty_available", safety_col: str = "safety_stock", reorder_col: str = "reorder_point") -> str:
    """CASE expression for inventory alert classification."""
    return (
        f"CASE\n"
        f"        WHEN {qty_col} <= 0 THEN 'OUT_OF_STOCK'\n"
        f"        WHEN {qty_col} <= {safety_col} THEN 'LOW_STOCK'\n"
        f"        WHEN {qty_col} <= {reorder_col} THEN 'REORDER'\n"
        f"        ELSE NULL\n"
        f"    END"
    )


def reconciliation_alert_sql(discrepancy_col: str = "discrepancy_pct") -> str:
    """CASE for reconciliation alert level."""
    threshold = PAYMENT_RECONCILIATION_THRESHOLD_PCT
    return (
        f"CASE\n"
        f"        WHEN {discrepancy_col} > {threshold * 3} THEN 'CRITICAL'\n"
        f"        WHEN {discrepancy_col} > {threshold} THEN 'WARNING'\n"
        f"        ELSE 'OK'\n"
        f"    END"
    )


def phone_normalize_sql(column: str = "phone") -> str:
    """SQL to normalize Vietnamese phone numbers to 0xx format."""
    return (
        f"CASE\n"
        f"        WHEN {column} LIKE '+84%' THEN '0' || SUBSTR(REPLACE(REPLACE({column}, ' ', ''), '-', ''), 4)\n"
        f"        WHEN {column} LIKE '84%' AND LENGTH(REPLACE(REPLACE({column}, ' ', ''), '-', '')) >= 11 "
        f"THEN '0' || SUBSTR(REPLACE(REPLACE({column}, ' ', ''), '-', ''), 3)\n"
        f"        ELSE REPLACE(REPLACE({column}, ' ', ''), '-', '')\n"
        f"    END"
    )
