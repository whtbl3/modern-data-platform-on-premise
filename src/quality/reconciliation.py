"""
Reconciliation: verify batch (Iceberg via Trino) and streaming (ClickHouse) agree.

Compares daily revenue totals between the two paths.
Used by Dagster reconciliation_check asset.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    metric: str
    batch_value: float
    stream_value: float
    discrepancy_pct: float
    is_within_threshold: bool


class BatchStreamReconciler:
    """Compares revenue between batch (Trino/Iceberg marts) and streaming (ClickHouse)."""

    def __init__(self, trino_resource=None, clickhouse_url: str = "http://clickhouse:8123"):
        self._trino_resource = trino_resource
        self._clickhouse_url = clickhouse_url

    def compare_daily_revenue(self, date: str) -> dict:
        batch_total = self._query_batch(date)
        stream_total = self._query_stream(date)

        if batch_total == 0 and stream_total == 0:
            pct = 0.0
        elif batch_total == 0:
            pct = 100.0
        else:
            pct = abs(batch_total - stream_total) / batch_total * 100

        return {
            "date": date,
            "batch_total": batch_total,
            "stream_total": stream_total,
            "discrepancy_pct": round(pct, 4),
        }

    def _query_batch(self, date: str) -> float:
        """Sum revenue from dbt mart fct_revenue_daily via Trino."""
        conn = self._trino_resource.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT COALESCE(SUM(gross_revenue), 0)
            FROM iceberg.analytics.fct_revenue_daily
            WHERE revenue_date = DATE '{date}'
        """)
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0

    def _query_stream(self, date: str) -> float:
        """Sum revenue from ClickHouse revenue_realtime."""
        import json
        import urllib.request

        query = (
            f"SELECT coalesce(sum(gross_revenue), 0) "
            f"FROM revenue_realtime "
            f"WHERE toDate(window_start) = '{date}' "
            f"FORMAT JSON"
        )
        req = urllib.request.Request(
            self._clickhouse_url,
            data=query.encode(),
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            rows = result.get("data", [])
            return float(rows[0]["coalesce(sum(gross_revenue), 0)"]) if rows else 0.0
