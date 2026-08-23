# Runbook: Revenue Reconciliation Drift

**Alert:** `RevenueReconciliationDrift`  
**Severity:** Critical  
**Impact:** Revenue numbers between batch (Trino/Iceberg) and streaming (ClickHouse) disagree by >1%. Finance dashboards may show incorrect totals.

## Context

The reconciliation compares:
- **Batch path:** Dagster → MinIO → Spark → Iceberg → dbt → `fct_revenue_daily`
- **Stream path:** Kafka → Flink → ClickHouse → `revenue_realtime`

A healthy system shows <0.1% drift (due to windowing boundaries). >1% indicates a real problem.

## Triage

```sql
-- Check today's numbers in both systems
-- Trino (batch):
SELECT SUM(gross_revenue) FROM iceberg.analytics.fct_revenue_daily
WHERE revenue_date = CURRENT_DATE;

-- ClickHouse (stream):
SELECT sum(gross_revenue) FROM revenue_realtime
WHERE toDate(window_start) = today();

-- Find which stores/channels have discrepancy
SELECT store_id, channel,
       batch_revenue, stream_revenue,
       abs(batch_revenue - stream_revenue) / batch_revenue * 100 as drift_pct
FROM iceberg.analytics.fct_reconciliation
WHERE reconciliation_date = CURRENT_DATE
  AND alert_level != 'OK'
ORDER BY drift_pct DESC;
```

## Common Causes

| Cause | Direction | Fix |
|-------|-----------|-----|
| Flink job was down for a period | Stream < Batch | Check Flink recovery, lag should catch up |
| Batch ingestion delayed | Batch < Stream | Wait for next Dagster run to complete |
| Duplicate events in Kafka | Stream > Batch | Check Flink exactly-once settings |
| Order filter logic diverged | Either direction | Compare `shared_logic/rules.py` with dbt macro |
| Late-arriving POS data | Batch > Stream | POS CSV arrived after streaming window closed |

## Resolution Steps

### 1. Identify the source

```bash
# Check if Flink had downtime today
kubectl get events -n lakehouse-prod --field-selector reason=Unhealthy \
  --sort-by='.lastTimestamp' | grep flink

# Check if Dagster had failures
uv run dagster job list-runs --status FAILURE --since "2026-08-23"
```

### 2. If stream is behind (Flink was down)

Wait for consumer lag to clear. The reconciliation will self-heal once Flink catches up.

### 3. If batch is behind (late data)

```bash
# Trigger a backfill for the missing date
uv run dagster job launch --job __ASSET_JOB --partition 2026-08-23
```

### 4. If logic diverged

```bash
# Verify shared rules are in sync
uv run pytest tests/test_shared_logic.py -v

# Compare filter SQL between batch and streaming
uv run python -c "from src.shared_logic.sql_templates import order_filter_sql; print(order_filter_sql())"
# Must match what dbt macro `order_filter()` produces
```

## Escalation

- Drift >1% for 1 hour: investigate root cause
- Drift >3% or persisting >4 hours: page data-engineering on-call
- Drift >5%: notify CFO/Finance team — revenue reports may be inaccurate
