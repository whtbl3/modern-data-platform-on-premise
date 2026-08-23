"""
Push gateway metrics for reconciliation and data quality.

Exposes custom metrics that PrometheusRule alerts can reference:
- lakehouse_reconciliation_discrepancy_pct
- lakehouse_raw_records_ingested_total
- lakehouse_dbt_run_duration_seconds
"""
import logging
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

PUSHGATEWAY_URL = "http://prometheus-pushgateway:9091"


def push_reconciliation_metric(date: str, batch_total: float, stream_total: float, discrepancy_pct: float):
    """Push reconciliation drift metric to Prometheus Pushgateway."""
    metrics = (
        f"# HELP lakehouse_reconciliation_discrepancy_pct Batch vs stream revenue drift percentage\n"
        f"# TYPE lakehouse_reconciliation_discrepancy_pct gauge\n"
        f'lakehouse_reconciliation_discrepancy_pct{{date="{date}",batch_total="{batch_total:.0f}",stream_total="{stream_total:.0f}"}} {discrepancy_pct}\n'
    )
    _push(metrics, job="reconciliation")


def push_ingestion_metric(asset_key: str, record_count: int, date: str):
    """Push ingestion count for freshness monitoring."""
    metrics = (
        f"# HELP lakehouse_raw_records_ingested_total Records ingested per asset per day\n"
        f"# TYPE lakehouse_raw_records_ingested_total gauge\n"
        f'lakehouse_raw_records_ingested_total{{asset_key="{asset_key}",date="{date}"}} {record_count}\n'
    )
    _push(metrics, job="ingestion", grouping={"asset_key": asset_key})


def push_dbt_duration(model: str, duration_seconds: float):
    """Push dbt model run duration."""
    metrics = (
        f"# HELP lakehouse_dbt_run_duration_seconds Duration of dbt model run\n"
        f"# TYPE lakehouse_dbt_run_duration_seconds gauge\n"
        f'lakehouse_dbt_run_duration_seconds{{model="{model}"}} {duration_seconds}\n'
    )
    _push(metrics, job="dbt", grouping={"model": model})


def _push(metrics_text: str, job: str, grouping: dict | None = None):
    """Push metrics to Prometheus Pushgateway."""
    path = f"/metrics/job/{job}"
    if grouping:
        for key, value in grouping.items():
            path += f"/{key}/{value}"

    url = f"{PUSHGATEWAY_URL}{path}"
    try:
        req = Request(url, data=metrics_text.encode(), method="POST")
        req.add_header("Content-Type", "text/plain")
        urlopen(req)
    except OSError as e:
        logger.warning(f"Failed to push metrics to {url}: {e}")
