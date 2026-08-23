# src/quality/

Data quality checks và batch/stream reconciliation.

## Cấu trúc

```
quality/
├── soda_checks.yml        # Soda Core quality rules per layer
├── reconciliation.py      # So sánh batch (Trino) vs streaming (ClickHouse) revenue
└── metrics_exporter.py    # Push custom metrics → Prometheus Pushgateway
```

## Files

| File | Vai trò |
|------|---------|
| `soda_checks.yml` | Quality rules cho tất cả tables: staging (7 tables), intermediate (2), marts (5). Checks: row_count, missing, duplicate, valid range, freshness |
| `reconciliation.py` | `BatchStreamReconciler`: query Trino (fct_revenue_daily) vs ClickHouse (revenue_realtime), tính discrepancy_pct. Dùng bởi Dagster `reconciliation_check` asset |
| `metrics_exporter.py` | Push metrics lên Prometheus Pushgateway: reconciliation drift %, ingestion counts, dbt duration. Cho PrometheusRule alerts |

## Reconciliation flow

```
Dagster (daily, after dbt_marts) 
    → reconciliation.py 
        → query Trino: SUM(gross_revenue) from fct_revenue_daily
        → query ClickHouse: SUM(gross_revenue) from revenue_realtime  
        → compute discrepancy_pct
        → if > 1%: log WARNING
        → push metric to Prometheus
        → PrometheusRule fires alert → Slack #finance-data
```

## Chạy manual

```bash
# Soda scan (cần Trino đang chạy)
uv run soda scan -d lakehouse -c src/quality/soda_checks.yml

# Quality checks cũng được chạy trong Dagster asset `dbt_tests`
```
