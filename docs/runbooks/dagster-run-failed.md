# Runbook: Dagster Run Failed

**Alert:** `DagsterRunFailed`  
**Severity:** Critical  
**Impact:** Data freshness degraded — downstream marts and dashboards may show stale data.

## Triage

1. Open Dagster UI: `http://dagster:3000/runs`
2. Find the failed run (red status)
3. Check the error in the run logs — identify which asset failed

## Common Causes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `raw_*` asset failed | Source unavailable or MinIO down | Check MinIO health, verify source connectivity |
| `dbt_staging` failed | Trino connection refused | `kubectl get pods -n lakehouse-prod -l app=trino` |
| `dbt_marts` failed | SQL error in model | Check dbt logs, fix model, re-run |
| `dbt_tests` failed | Data quality issue | See [dbt-test-failure.md](./dbt-test-failure.md) |
| OOM killed | Insufficient memory for partition | Reduce partition size or increase executor memory |

## Resolution Steps

```bash
# 1. Check pod health
kubectl get pods -n lakehouse-prod | grep -v Running

# 2. Re-launch failed run (specific partition)
uv run dagster job launch --job __ASSET_JOB --partition 2026-08-23

# 3. If source was temporarily unavailable, backfill
uv run dagster job backfill --job __ASSET_JOB --from 2026-08-20 --to 2026-08-23
```

## Escalation

- If repeated failures (3+ in 24h): escalate to on-call engineer
- If revenue-impacting (fct_revenue_daily stale): notify CFO team via #finance-data Slack
